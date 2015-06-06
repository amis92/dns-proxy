# dns-proxy
DNS proxy written in Python as an academic exercise.


To run default proxy app, run the package like so:
```sh
$ python -m dnsproxy
```
or run app module
```sh
$ python dnsproxyapp
```

Either way, you will have to do it as admin with default config:
- the proxy binds to port 53 if not changed.

## Dependencies

This package requires following packages:
	* `dnspython`,
	* `dnslib` and
	* 'Flask`.