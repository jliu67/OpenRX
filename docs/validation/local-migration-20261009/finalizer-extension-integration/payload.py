import pathlib,sys
out=pathlib.Path(sys.argv[1]);out.mkdir()
(out/'scientific.txt').write_text('finite retained toy output\n')
print('tiny payload complete',flush=True)
