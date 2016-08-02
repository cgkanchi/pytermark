import os
import sys
import click
from tqdm import tqdm
from PIL import Image, ImageFont, ImageDraw
import glob

# hack to allow wildcard args in windows
if sys.platform == 'win32':
    infile_type = click.Path()
else:
    infile_type = click.Path(exists=True)
@click.command()
@click.argument('infile', type=infile_type, nargs=-1)
@click.argument('text', required=True)
@click.option('--location', '-l', default='center', type=click.Choice(['lower-left', 'upper-left', 'upper-right',
                                                                       'lower-right', 'center', 'centre',
                                                                       'll', 'ul', 'ur', 'lr', 'c']), help='Location of watermark.')
@click.option('--transparency', '-t', type=click.IntRange(0, 255), default=32,
              help='How transparent you want your watermark to be. Select a value between 0 (completely transparent) and 255 (completely opaque).')
@click.option('--inplace', is_flag=True, default=False, help='Overwrite input images.')
@click.option('--out-type', type=click.Choice(['jpeg', 'jpg', 'png', 'tiff', 'tif', 'input']), default='input', help='Output file type. Default is the same as input')
@click.option('--jpeg-quality', '-q', type=click.IntRange(1, 100), default=100,
              help='JPEG quality setting. Default is 100. Ignored if out-type is not jpeg/jpg.')
@click.option('--font',
              help='Font to use. If font file doesn\'t exist, raises an error. On Linux, you may have to specify the full path of the font file.')
@click.option('--size', default='auto',
              help='Size of watermark. Can be an integer or one of small, medium, large or auto. Default is auto.')
@click.option('--text-color', default='white', help='Color name. Currently only "white" and "black" are supported.')
def watermark(infile, text, location, transparency, inplace, out_type, jpeg_quality, font, size, text_color):
    if sys.platform == 'win32':
            # hack for windows to handle wildcards
            infile = list(_ljoin([glob.glob(i) for i in infile if '*' in i]) + [i for i in infile if '*' not in i])
    print('Found {} files to process'.format(len(infile)))
    for f in tqdm(infile):
        _watermark(f, text, location, transparency, inplace, out_type, jpeg_quality, font, size, text_color)
    print('Done!')


def _ljoin(lol):
    '''Return a flattened list from a list of lists - only goes one level deep (by design) and ignores iterables that are not lists or tuples (also by design)'''
    flat = []
    for l in lol:
        if isinstance(l, list) or isinstance(l, tuple):
            flat.extend(l)
        else:
            flat.append(l)
    return flat

def _watermark(infile, text, location, transparency, inplace, out_type, jpeg_quality, font, size, text_color, return_image=False):
    if not inplace:
        splitname = os.path.splitext(infile)
        if out_type and out_type != 'input':
            splitname = list(splitname[:-1])
            splitname.append('.{}'.format(out_type))

        outfilename = '{}_watermarked{}'.format(*splitname)
    else:
        outfilename = infile

    img = Image.open(infile).convert('RGBA')
    width, height = img.size
    if sys.platform == 'linux' and not font:
        font_path = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
    elif sys.platform == 'win32' and not font:
        font_path = 'times.ttf'
    else:
        font_path = font

    if size.lower() in ['auto', 'large', 'medium', 'small']:
        # magic calculation for font size
        font_size = _get_ideal_font_size(text, width, size, font_path)
    else:
        font_size = int(size)

    font = ImageFont.truetype(font_path, font_size)
    # create a fully transparent image
    fill = (0, 0, 0, transparency) if text_color.lower() == 'black' else (255, 255, 255, transparency)

    txt_image = Image.new('RGBA', img.size, (255, 255, 255, 0))
    text_size = ImageFont.truetype(font_path, font_size).getsize(text)
    d = ImageDraw.Draw(txt_image)
    d.text(_get_ideal_location(text_size, (width, height), location), text, font=font, fill=fill)
    out_img = Image.alpha_composite(img, txt_image)
    extra_args = {}
    if out_type in ('jpg', 'jpeg'):
        extra_args = {'subsampling': 0, 'quality': jpeg_quality}
    out_type = 'jpeg' if out_type == 'jpg' else out_type
    if out_type == 'input':
        out_type = None

    out_img.save(outfilename, format=out_type, **extra_args)


def _get_ideal_location(text_size, image_size, location):
    img_width, img_height= image_size
    text_width, text_height= text_size

    if location in ('upper-left', 'ul'):
        return (0, 0)
    elif location in ('upper-right', 'ur'):
        return (img_width - text_width, 0)
    elif location in ('lower-right', 'lr'):
        return (img_width - text_width, img_height - text_height)
    elif location in ('lower-left', 'll'):
        return (0, img_height - text_height)
    elif location in ('center', 'centre', 'c'):
        return (img_width//2 - text_width//2, img_height//2 - text_height//2)


def _get_ideal_font_size(text, img_width, size_spec, font_path):
    font_ratio_map = {'auto': 0.5, 'medium': 0.5, 'small': 0.2, 'large': 0.8}
    # get the size of text at 1 point
    text_width, text_height = ImageFont.truetype(font_path, 1).getsize(text)
    font_size = int(font_ratio_map[size_spec] * img_width/text_width)
    return font_size


if __name__ == '__main__':
    watermark()

