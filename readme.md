# Jenkins-Certbot
## Pre-Requisites
* Create a Digital Ocean API key to use. This should be configured with write privileges
* Generate an SSH key for the script to use to execute commands on the droplets. The private key can be dropped in the same folder as main.py. Should be saved as `id_rsa`

## Debug Execution
`python3 .\main.py --apikey "example" --requesteddomain "testdk" --rootdomain "romanrii.com" --requiredemail "roman.rivas@romanrii.com"`
