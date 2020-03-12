# Online Judge Template Generator

## Architecture

1.  download and recognize HTML with [requests](https://requests.readthedocs.io/en/master/) + [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
1.  parse the `<pre>` format in old style Lex + Yacc ([ply](http://www.dabeaz.com/ply/))
1.  generate codes with a template engine ([Mako](https://www.makotemplates.org/))

## License

MIT
