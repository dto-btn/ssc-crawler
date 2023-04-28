# ssc crawler

Used to do PoC and crawl certain content from SSC site(s)

## how-to

Using python virtual environments to work with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

Run with `python crawler.py`. 

### docker

Build the image and then run it `docker build -t crawler .`

Then ` docker run -it -v $(pwd)/dump:/usr/src/app/dump crawler` 