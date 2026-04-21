from PIL import Image, ImageDraw

def add_watermark(input_path, output_path, text):
    img = Image.open(input_path).convert("RGBA")

    overlay = Image.new("RGBA", img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    draw.text((width-250, height-50), text, fill=(255,0,0,120))

    watermarked = Image.alpha_composite(img, overlay)
    watermarked.convert("RGB").save(output_path)

    return output_path