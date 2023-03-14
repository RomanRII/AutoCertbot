# Auto Certbot
## Pre-Requisites
* Create a Digital Ocean API key to use. This should be configured with write privileges
* Generate an SSH key for the script to use to execute commands on the droplets. The private key must be in the cwd when executed. The key must be saved as `id_rsa`
  * This can be adjusted on https://github.com/RomanRII/AutoCertbot/blob/main/helper.py#L96
  
## Notes
* This will leave a residual DNS record in digital ocean pointing at the non-existant droplet. This is left so the consultant/user can easily modify the record to point to the appropiate destination or remove manually.

## Execution
`python3 .\main.py --apikey "DOAPIKEY" --requesteddomain "sub.domain" --rootdomain "example.com" --requiredemail "first.last@example.com" `

![image](https://user-images.githubusercontent.com/74742067/225129539-32e0f746-423d-4296-af7c-9c98a0d6d5bc.png)
![image](https://user-images.githubusercontent.com/74742067/225129624-45f8999e-9ba3-4043-a7b7-6b45f51f3c19.png)
