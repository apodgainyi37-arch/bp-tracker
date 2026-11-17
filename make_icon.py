from PIL import Image, ImageDraw

def create_heart_ecg_icon(filename="icon.png", size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Темный скругленный фон
    draw.rounded_rectangle([16, 16, size - 16, size - 16], radius=110, fill=(24, 28, 38, 255))

    # Сердце
    r = 105
    left_center, right_center = (185, 200), (327, 200)
    draw.ellipse([left_center[0] - r, left_center[1] - r, left_center[0] + r, left_center[1] + r], fill=(229, 57, 53, 255))
    draw.ellipse([right_center[0] - r, right_center[1] - r, right_center[0] + r, right_center[1] + r], fill=(229, 57, 53, 255))
    draw.polygon([(86, 235), (426, 235), (256, 425)], fill=(229, 57, 53, 255))
    draw.polygon([(80, 200), (92, 250), (256, 250), (256, 200)], fill=(229, 57, 53, 255))
    draw.polygon([(432, 200), (420, 250), (256, 250), (256, 200)], fill=(229, 57, 53, 255))

    # Белая линия пульса (ЭКГ)
    ecg_points = [
        (75, 255), (170, 255), (195, 220), (215, 280),
        (245, 145), (275, 345), (305, 215), (325, 255), (437, 255)
    ]
    draw.line(ecg_points, fill=(255, 255, 255, 255), width=18, joint="curve")
    img.save(filename)

if __name__ == "__main__":
    create_heart_ecg_icon()