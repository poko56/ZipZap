from PIL import Image
img = Image.open('app_icon_source.jpg')
# Make it square if it isn't
width, height = img.size
min_dim = min(width, height)
left = (width - min_dim)/2
top = (height - min_dim)/2
right = (width + min_dim)/2
bottom = (height + min_dim)/2
img = img.crop((left, top, right, bottom))
img.save('icon.png')
img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
