import base64


def create_qr():
    test = ""
    imgdata = base64.b64decode(test)
    file = open('qr.jpg', 'wb')
    file.write(imgdata)
    file.close()


if __name__ == '__main__':
    create_qr()
