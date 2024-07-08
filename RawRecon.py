import os
import sys
import shutil
import dns.resolver

def check_command(cmd):
    if shutil.which(cmd) is None:
        print(f"Error: {cmd} is not installed or not in your PATH.")
        sys.exit(1)

# Ensure required commands are available
required_commands = [
    'subfinder', 'assetfinder', 'sublist3r', 'knockpy', 'massdns',
    'httpx-toolkit', 'masscan', 'nuclei'
]

for cmd in required_commands:
    check_command(cmd)

# Install waybackurls if not available
if shutil.which('waybackurls') is None:
    print("Installing waybackurls...")
    os.system("go install github.com/tomnomnom/waybackurls@latest")
    os.environ["PATH"] += os.pathsep + os.path.expanduser("~") + "/go/bin"
    if shutil.which('waybackurls') is None:
        print("Failed to install waybackurls.")
        sys.exit(1)

if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
    print("Usage: python script.py [OPTIONS] TARGET [ALL_DOMAINS]")
    print("OPTIONS:")
    print("  -n, --no-bruteforce   Skip the bruteforce domains using MassDNS")
    print("  -N, --nuclei          Run Nuclei for vulnerability scanning")
    sys.exit()

skip_bruteforce = False
run_nuclei = False
target = None
alldomains = None

for i, arg in enumerate(sys.argv[1:]):
    if arg in ['-n', '--no-bruteforce']:
        skip_bruteforce = True
    elif arg in ['-N', '--nuclei']:
        run_nuclei = True
    elif target is None:
        target = arg
    elif alldomains is None:
        alldomains = arg

# Get subdomains from subfinder
print("[-] Running Subfinder...")
os.system(f"subfinder -d {target} -silent > subdomains1.txt")
print("[+] Subfinder tool result saved in subdomains1.txt")

# Get subdomains from assetfinder
print("[-] Running Assetfinder...")
os.system(f"assetfinder {target} -subs-only > subdomains2.txt")
print("[+] Assetfinder tool result saved in subdomains2.txt")

# Get subdomains from sublist3r
print("[-] Running Sublist3r...")
os.system(f"sublist3r -n -d {target} -o subdomains3.txt")
print("[+] Sublist3r tool result saved in subdomains3.txt")

if not skip_bruteforce:
    # Get subdomains from knockpy
    print("[-] Running Knockpy...")
    os.system(f"knockpy --no-http {target}")
    os.system(f"cat knockpy_report/{target}* | grep -oP '[a-z0-9]+\.'{target} | sort -u | uniq > subdomains5.txt")
    print("[+] Knockpy tool result saved in subdomains5.txt")
    # Bruteforce subdomains
    print("[-] Running MassDNS...")
    os.system(f"awk -v host={target} '{{print $0\".\"host}}' /usr/share/SecLists/Discovery/DNS/bitquark-subdomains-top100000.txt > massdnslist")
    os.system("massdns massdnslist -r /usr/share/SecLists/Miscellaneous/dns-resolvers.txt -o S -t A -q | awk -F\". \" '{{print $1}}' | sort -u > subdomains6.txt")
    print("[+] MassDNS tool result saved in subdomains6.txt")
else:
    print("[-] Skipping MassDNS Bruteforce step...")

# Sort and organize the outputs
print("[+] Sorting the result in one file 'finaldomains.txt'")
os.system(f"cat subdomains*.txt | grep -i {target} | sort -u | uniq > finaldomains.txt")
os.system(f"rm subdomains*.txt")
print(f"[+] Domains found: {len(open('finaldomains.txt').readlines())}")
print("[+] Tool finished getting all subdomains")

if alldomains is None:
    alldomains = "finaldomains.txt"

#
# Httpx
#
print("[-] Running Httpx...")
os.system(f"httpx-toolkit -l {alldomains} -silent -timeout 20 -title -td -status-code -follow-redirects -o alive_titles.txt")
print("[+] Saved Into alive_titles.txt...")
os.system(f"cat alive_titles.txt | cut -d ' ' -f 1 > alive.txt")
print("[+] Saved Into alive.txt...")

#
# WaybackUrls
#

print("[-] Running waybackurls...")
with open("alive.txt", "r") as f:
    urls = f.readlines()

with open("wayback.txt", "w") as wayback_output:
    for url in urls:
        os.system(f"echo '{url.strip()}' | waybackurls >> wayback.txt")
print("[+] Wayback URLs saved in wayback.txt")

#
# Masscan
#

def resolve_to_ip(domain):
    try:
        result = dns.resolver.resolve(domain, 'A')
        return [ip.address for ip in result]
    except Exception as e:
        print(f"Could not resolve {domain}: {e}")
        return []

# Preprocess alive.txt to extract domain names and resolve to IP addresses
with open("alive.txt", "r") as f:
    alive_domains = [url.split("//")[-1].split("/")[0].strip() for url in f.readlines()]

alive_ips = []
for domain in alive_domains:
    alive_ips.extend(resolve_to_ip(domain))

with open("alive_for_masscan.txt", "w") as f:
    f.write("\n".join(alive_ips))

if not alive_ips:
    print("No valid IPs found for Masscan.")
    sys.exit(1)

print("[-] Running Port Scanning with Masscan...")
os.system(f"masscan -iL alive_for_masscan.txt --rate 1000 -oX masscan.xml") # SPECIFY THE PORT IS NEEDED
print("[+] Masscan results saved in masscan.xml")
os.system(f"cat masscan.xml")

#
# Nuclei
#

if run_nuclei:
    print("[-] Running Nuclei...")
    os.system("nuclei -l alive.txt -silent -o aliveNuclei.txt")
    print("[+] Nuclei results saved in aliveNuclei.txt")
else:
    print("[-] Skipping Nuclei step...")
