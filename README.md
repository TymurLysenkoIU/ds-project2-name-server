# Deployment

## Docker

### Build docker image

From the current folder run:

```sh
docker build --tag sitiritis/ds-dfs-name-server -f ./docker/Dockerfile .
```

### Run a container

The API will be available to port **80**, so this port of the container has to be mapped to some port on the host operating system.

```sh
docker run -p 8000:80 --name name-server sitiritis/ds-dfs-name-server
```

### Environment variables

- `DJANGO_SECRET_KEY` - secret key to be used for the application
- `MONGO_HOST` - Host address and port of mongodb, which will be used without protocol specification. Default is **mongo:27017**.
- `MONGO_USER` - Mongodb user name to be used by the server. Default is **admin**.
- `MONGO_PASS` - Password of the mongodb user. Default is **mongo**.
- `FTP_USER` - Name of the FTP user on storage servers. The save account is used on each server. Default is **ftpuser**.
- `FTP_PASS` - FTP user password on storage server. The save account is used on each server. Default is **ftp-pass**.
- `STORAGE_REQUEST_TIMEOUT` - How long to wait in seconds before deciding that a storage node has disconnected. Default is **1**.
