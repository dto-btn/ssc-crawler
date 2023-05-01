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

## install chrome-browser-stable on wsl2

You need to install `chrome-browser-stable` via [this link](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps#install-google-chrome-for-linux) and [this link](https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md#running-puppeteer-on-wsl-windows-subsystem-for-linux)

```bash
# follow instructions above
# then install missing libs.
sudo apt update
sudo apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget
```