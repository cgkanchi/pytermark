import os
import sys
import click
from tqdm import tqdm
from PIL import Image
import glob

# hack to allow wildcard args in windows
if sys.platform == 'win32':
    infile_type = click.Path()
else:
    infile_type = click.Path(exists=True)

@click.command()
@click.argument('infile', type=infile_type, nargs=-1)
@click.option('--jpeg-quality', '-q', type=click.IntRange(1, 100), default=100,
              help='JPEG quality setting. Default is 100.')
@click.option('--crop-from', '-c', type=click.Choice(['top', 'bottom', 'equal', 't', 'b', 'e']), default='e',
              help='Crop from top, bottom or equally from both. Default is equal.')
def cropper(infile, jpeg_quality, crop_from):
    if sys.platform == 'win32':
            # hack for windows to handle wildcards
            infile = list(_ljoin([glob.glob(i) for i in infile if '*' in i]) + [i for i in infile if '*' not in i])
    print('Found {} files to process'.format(len(infile)))
    for f in tqdm(infile):
        _cropper(f, jpeg_quality, crop_from)
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

def _cropper(infile, jpeg_quality, crop_from):
    splitname = os.path.splitext(infile)
    ext = splitname[-1]
    splitname = list(splitname[:-1])
    splitname.append('.{}'.format(ext))
    outfilename = '{}_cropped{}'.format(*splitname)


    img = Image.open(infile).convert('RGBA')
    w, h = img.size

    target_w = 16
    target_h = 9

    crop_amt = -(target_h * w - target_w * h)/(target_w)

    if crop_from in ('top', 't'):
        ca_top = crop_amt
        ca_bottom = 0
    elif crop_from in ('bottom', 'b'):
        ca_top = 0
        ca_bottom = crop_amt
    else:
        ca_top = ca_bottom = crop_amt/2
    out_img = img.crop([0, ca_top, w, h - ca_bottom])

    extra_args = {}
    if ext.lower() in ('jpg', 'jpeg'):
        extra_args = {'subsampling': 0, 'quality': jpeg_quality}

    out_img.save(outfilename, **extra_args)


if __name__ == '__main__':
    cropper()

