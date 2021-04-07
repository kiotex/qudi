def read_header(header_filepath):
    ret = {}

    with open(header_filepath, mode='r') as f:
        lst = [s.strip() for s in f.readlines()]

    comment_flg = False
    for l in lst:
        items = l.split()

        # 複数行コメントの除去
        if len(items) != 0 and items[0] == "/*":
            comment_flg = True
            continue
        if comment_flg is True:
            if len(items) != 0 and items[0] == "*/":
                comment_flg = False
            continue

        # 単行コメントの除去
        if len(items) != 0 and ("//" in items[0]):
            continue

        # 字書型に格納する
        if len(items) == 3:
            if items[0] == "#define" or items[1] == "=":
                if "x" in items[2]:
                    val = int(items[2].replace(',', ''), 16)
                    #val = val.to_bytes((val.bit_length() + 7) // 8, byteorder='big')
                else:
                    val = float(items[2].replace(',', ''))

                if items[0] == "#define":
                    ret[items[1]] = val
                elif items[1] == "=":
                    ret[items[0]] = val
    return ret


if __name__ == "__main__":
    ret = read_header(r"hardware\diy_daq\MAX11300Hex_20210406.h")
    ret
