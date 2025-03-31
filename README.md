# apache-archive-downloader

## Usage

```shell
python run.py [-h] --url URL --username USERNAME --password PASSWORD [--output OUTPUT]
```

You can put your password in the `.pass` file and run the script like this:
```shell
python run.py [-h] --url URL --username USERNAME --password $(cat .pass)$ [--output OUTPUT]
```

## Details

Downloads all compressed files from `URL` into `OUTPUT`.

Goes recursively through all links found on the page.

Requires HTTP Basic Auth of the web server.

Supports continuation of partly downloaded files.

## Todo

- [ ] Check if file was modified on server. If so, download it again. If partly downloaded, start downloading from beginning.