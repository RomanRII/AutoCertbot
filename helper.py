from digitalocean import Firewall, InboundRule, OutboundRule, Destinations, Sources, Manager, Droplet, Domain
from nslookup import Nslookup
import paramiko
import time

class doApi:

	def entry(doApiKey, requestedDomain, rootDomain, requiredEmail):
		ipAddress, dropletID = doApi.createDroplet(doAPIKey=doApiKey)
		firewallID = doApi.addFirewall(doApiKey=doApiKey, dropletID=dropletID)
		doApi.addDNSRecord(doApiKey=doApiKey, dropletIP=ipAddress, requestedDomain=requestedDomain, rootDomain=rootDomain)
		pubCert, keyCert = doApi.executeDroplet(dropletIP=ipAddress, requestedHostname=requestedDomain, rootDomain=rootDomain, requiredEmail=requiredEmail)
		doApi.cleanupDO(doAPIKey=doApiKey, dropletID=dropletID, firewallID=firewallID)

		print("Public Certificate:\n")
		for pubLine in pubCert:
			pubLine = pubLine.strip('\n')
			print(pubLine)
		print("\nPrivKey Certificate:\n")
		for privLine in keyCert:
			privLine = privLine.strip('\n')
			print(privLine)

	# 1. Create the droplet and get the IPv4 address.
	def createDroplet(doAPIKey):
		print("[+] Creating the droplet")
		manager = Manager(token=doAPIKey)
		keys = manager.get_all_sshkeys()

		droplet = Droplet(token=doAPIKey,
                            	name='Jenkins-Automated-Certbot',
                            	region='nyc2', # New York 2
                            	image='ubuntu-20-04-x64', # Ubuntu 20.04 x64
                            	size_slug='s-1vcpu-1gb',  # 1GB RAM, 1 vCPU
			       				ssh_keys=keys,
                            	backups=False)
		droplet.create()
		print("[+] Droplet is now being created.. This should take <40 seconds")
		time.sleep(40)
		actions = droplet.get_actions()
		for action in actions:
			action.load()
			# Once it shows "completed", droplet is up and running
			if (action.status == "completed"):
				print("[+] Droplet has been created")
			else:
				print("[-] Droplet creation has failed")
				exit()
			
			dropletData = droplet.get_data("droplets/%s" % droplet.id)
			dropletObj = dropletData['droplet']
			ipAddress = dropletObj["networks"]["v4"][0]["ip_address"]
			return ipAddress, droplet.id

	# 2. Create a firewall rule to allow port 22-80 inbound to the droplet. (DO API only allowed single port, port range, or ALL. 22-80 had to be used)
	def addFirewall(doApiKey, dropletID):
		inbound_rule = InboundRule(protocol="tcp", ports="22-80", sources=Sources(addresses=["0.0.0.0/0","::/0"]))
		outbound_rule = OutboundRule(protocol="tcp", ports="all",destinations=Destinations(addresses=["0.0.0.0/0","::/0"]))
		firewall = Firewall(token=doApiKey,name="CertbotPy-FW",inbound_rules=[inbound_rule],outbound_rules=[outbound_rule],droplet_ids=[dropletID])
		firewall.create()
		print("[+] Firewall rule created")
		return firewall.id
				
	# 3. Add the IPv4 address to the DNS record. Point the record to the requested domain
	def addDNSRecord(doApiKey, dropletIP, requestedDomain, rootDomain):
		doDomain = Domain(token=doApiKey, name=rootDomain)

		newRecord = doDomain.create_new_domain_record(
			type='A',
			name=requestedDomain,
			data=dropletIP
		)

		print("[+] Record created. Waiting for record to show valid.")

		valid = False
		while(valid == False):
			dnsQuery = Nslookup(dns_servers=["8.8.8.8"])
			try:
				ipRecord = dnsQuery.dns_lookup(requestedDomain + '.' + rootDomain)
				print("[+] Record resolved: %s" % (ipRecord.answer[0]))
				valid = True
				print("[+] DNS record created")
			except:
				valid = False
				print("[!] Record did not resolve. Waiting 10 seconds.")
				time.sleep(10)
		

	# 4. Execute the required commands to install certbot and request the cert.
	def executeDroplet(dropletIP, requestedHostname, rootDomain, requiredEmail):
		dropletClient = paramiko.SSHClient()
		dropletClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		print("[*] Waiting for the SSH service to start")
		time.sleep(10)
		dropletClient.connect(dropletIP, username='root', key_filename="./id_rsa")
		print("[*] Updating host")
		stdin, stdout, stderr = dropletClient.exec_command("apt --yes update")
		exit_status = stdout.channel.recv_exit_status()
		
		if exit_status == 0:
			print("[+] Host successfully updated")
		else:
			print("[-] Host failed to update")
			exit()
		
		print("[*] Installing snap core")
		stdin, stdout, stderr = dropletClient.exec_command("snap install core")
		exit_status = stdout.channel.recv_exit_status()
		if exit_status == 0:
			print("[+] Host installed snap core")
		else:
			print("[-] Host failed to install snap core")
			exit()

		print("[*] Refreshing snap core")		
		stdin, stdout, stderr = dropletClient.exec_command("snap refresh core")
		exit_status = stdout.channel.recv_exit_status()
		if exit_status == 0:
			print("[+] Host successfully refreshed snap core")
		else:
			print("[-] Host failed to refresh snap core")
			exit()

		print("[*] Installing certbot")
		stdin, stdout, stderr = dropletClient.exec_command("snap install --classic certbot")
		exit_status = stdout.channel.recv_exit_status()
		if exit_status == 0:
			print("[+] Host successfully installed certbot")
		else:
			print("[-] Host failed to install certbot")
			exit()

		print("[*] Requesting SSL certificate")
		requestCert = "/snap/bin/certbot certonly --standalone -d '%s' -m '%s' --agree-tos --non-interactive" % (requestedHostname + '.' + rootDomain, requiredEmail)
		stdin, stdout, stderr = dropletClient.exec_command(requestCert)
		exit_status = stdout.channel.recv_exit_status()
		if exit_status == 0:
			print("[+] Host requested the certificate successfully")
		else:
			print("[-] Host failed to request the certificate")
			exit()
		
		readPubCert = "cat /etc/letsencrypt/live/%s/fullchain.pem" % (requestedHostname + '.' + rootDomain)
		readKeyCert = "cat /etc/letsencrypt/live/%s/privkey.pem" % (requestedHostname + '.' + rootDomain)
		stdin, pubCertOut, stderr = dropletClient.exec_command(readPubCert)
		stdin, keyOut, stderr = dropletClient.exec_command(readKeyCert)
		
		retPubCert = pubCertOut.readlines()
		retKeyCert = keyOut.readlines()
		dropletClient.close()

		return retPubCert, retKeyCert
	
	# 5. Cleanup. Remove the droplet, firewall and DNS record. 
	def cleanupDO(doAPIKey, dropletID, firewallID):
		droplet = Droplet(token=doAPIKey, id=dropletID)
		droplet.destroy()
		print("[+] Droplet destroyed")
		firewall = Firewall(token=doAPIKey, id=firewallID)
		firewall.destroy()
		print("[+] Firewall destroyed")
