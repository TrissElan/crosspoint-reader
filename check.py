import struct
for font in ["pretendard_10","pretendard_12","pretendard_14","kopub_10","kopub_12","kopub_14"]:
    with open(f"crosspoint-reader-cjk-minimized/lib/EpdFont/builtinFonts/{font}.epdfont", "rb") as f:
        f.seek(8)
        aY  = struct.unpack('B', f.read(1))[0]
        asc = struct.unpack('b', f.read(1))[0]
        dsc = struct.unpack('b', f.read(1))[0]
        print(f"{font}: advanceY={aY}, ascender={asc}, descender={dsc}, gap={aY-(asc-dsc)}")