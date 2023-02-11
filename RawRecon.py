import os
import sys

if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
    print("Usage: python script.py [OPTIONS] TARGET [ALL_DOMAINS]")
    print("OPTIONS:")
    print("  -n, --no-bruteforce   Skip the bruteforce domains using MassDNS")
    sys.exit()

skip_bruteforce = False
target = None
alldomains = None

for i, arg in enumerate(sys.argv[1:]):
    if arg in ['-n', '--no-bruteforce']:
        skip_bruteforce = True
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

# Get subdomains from findomain
print("[-] Running Findomain...")
os.system(f"findomain-linux -t {target} -q > subdomains4.txt")
print("[+] Findomain tool result saved in subdomains4.txt")


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



print("[-] Running Httpx...")
os.system(f"httpx -l {alldomains} -silent -timeout 20 --silent -timeout 20 -title -tech-detect -status-code -follow-redirects -o alive_titles.txt")
print("[+] Saved Into alive_titles.txt...")
os.system(f"cat alive_titles.txt | cut -d ' ' -f 1 > alive.txt")
print("[+] Saved Into alive.txt...")

print("[-] Running waybackurls...")
with open("alive.txt", "r") as f:
    urls = f.readlines()

    for url in urls:
        os.system(f"waybackurls {url} >> wayback.txt")

print("[+] Wayback URLs saved in wayback.txt")

print("[-] Running Port Scanning...")
os.system(f"nmap -Pn -iL alive.txt >> nmap.txt")
os.system(f"cat nmap.txt")
print("[+] Saved Into nmap.txt...")

print("[-] Running Nuclei...")
os.system("nuclei -l alive.txt -silent -o aliveNuclei.txt")
print("[-] Saved Into nucleiAlive.txt...")
