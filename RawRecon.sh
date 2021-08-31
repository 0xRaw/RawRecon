#!/bin/bash

if [ -z $1 ]
	then
		echo "USAGE: ./RawEnum.sh [domain] (optional: subdomains file to skip first stage)"
		exit
	else
		target=$1
fi

if [ -z $2 ]
then
	# Get subdomains from subfinder
	echo -e "\e[31m[-]\e[0m Running Subfinder..."
    subfinder -d $target -silent > subdomains1.txt
	echo -e "\e[32m[+]\e[0m Subfinder tool result saved in subdomains1.txt" 

	# Get subdomains from assetfinder
    echo -e "\e[31m[-]\e[0m Running Assetfinder..."
	assetfinder $target -subs-only > subdomains2.txt
	echo -e "\e[32m[+]\e[0m Assetfinder tool result saved in subdomains2.txt"

	# Get subdomains from sublist3r
    echo -e "\e[31m[-]\e[0m Running Sublist3r..."
  sublist3r -n -d $target -o subdomains3.txt
	echo -e "\e[32m[+]\e[0m sublist3r tool result saved in subdomains3.txt" 

	# Get subdomains from findomain
    echo -e "\e[31m[-]\e[0m Running Findomain..."
  findomain-linux -t $target -q > subdomains4.txt
	echo -e "\e[32m[+]\e[0m findomain tool result saved in subdomains4.txt" 

	# Get subdomains from knockpy
    echo -e "\e[31m[-]\e[0m Running Knockpy..."
	knockpy --no-http $target
	cat knockpy_report/$target* | grep -oP '[a-z0-9]+\.'$target | sort -u | uniq > subdomains5.txt
	echo -e "\e[32m[+]\e[0m knockpy tool result saved in subdomains5.txt"

	# bruteforce subdomains 
    echo -e "\e[31m[-]\e[0m Running MassDNS..."
	awk -v host=$target '{print $0"."host}' /usr/share/SecLists/Discovery/DNS/bitquark-subdomains-top100000.txt > massdnslist
	massdns massdnslist -r /usr/share/SecLists/Miscellaneous/dns-resolvers.txt -o S -t A -q | awk -F". " '{print $1}' | sort -u  > subdomains6.txt
	echo -e "\e[32m[+]\e[0m massdns tool result saved in subdomains6.txt" 

	# sort and organize the outputs
	echo -e "\e[32m[+]\e[0m Sorting the result in one file 'finaldomains.txt'"
	cat subdomains*.txt | grep -i $target | sort -u | uniq > finaldomains.txt
	echo -e "\e[32m[+]\e[0m Domains found: \e[31m"$(cat finaldomains.txt | wc -l)
    echo -e "\e[0m"
	echo -e "\e[32m[+]\e[0m Tool finished getting all subdomains"
	alldomains=finaldomains.txt
	rm -rf subdomains*.txt
else
	alldomains=$2
fi
	echo -e "\e[32m[+]\e[0m Getting alive domains ..."
	/usr/local/bin/httpx -l $alldomains -silent -timeout 20 -title -tech-detect -status-code -follow-redirects -o alive_titles.txt
	echo -e "\e[32m[+]\e[0m Details of alive domains saved in 'alive_titles.txt' file"
	cat alive_titles.txt | cut -d ' ' -f 1 > alive.txt
	echo -e "\e[32m[+]\e[0m Alive domains saved in 'alive.txt' file"

	echo -e "\e[32m[+]\e[0m Using waybackurls tool with alive.txt..."
	cat alive.txt | /usr/local/bin/waybackurls > wayback_temp.txt
	cat wayback_temp.txt | grep -i $target | sort -u | uniq > waybackUrls.txt
	rm wayback_temp.txt
	echo -e "\e[32m[+]\e[0m waybackurls tool results saved in 'waybackUrls.txt'"
    echo -e "\e[31m[-]\e[0m Running Nuclei on alive.txt"
    nuclei -l alive.txt  -silent -o aliveNuclei.txt
    echo -e "\e[32m[+]\e[0m nuclei output saved in 'aliveNuclei.txt'"
    echo -e "\e[32m[+]\e[0m Screenshotting for alive domains"
	webscreenshot -i $1
	echo "[+] screenshots saved!"
	for i in $(ls ./screenshots/); do echo $i; firefox ./screenshots/$i;done
