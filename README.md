# adhoc-pexip

## to run stand-alone:
run [certbot](https://certbot.eff.org/) first to get certs:
```
	pexip_server=pexip-management-server.example.com \
	pexip_password="pexip_admin_password" \
	pexip_url=meeting.example.com \
	cas_server=cas-server.example.com \
	smtp_server=mail.example.com \
	smtp_sender="meeting@example.com" python app.py
```
