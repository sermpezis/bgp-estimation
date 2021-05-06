#!/bin/bash

#1) ['amsterdam01', 'uw01'], catchment: ~25/75
#2) ['grnet01', 'uw01'], catchment: ~25/75
#3) ['ufmg01', 'uw01'], catchment: ~20/80
#4) ['phoenix01', 'uw01'], catchment: ~15/85
#5) ['grnet01', 'seattle01'], catchment: ~15/85
#6) ['seattle01', 'ufmg01'], catchment: ~10/90
#7) ['seattle01', 'uw01'], , catchment: ~10/90

#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
##1) ['amsterdam01', 'uw01'], catchment: ~25/75
#echo "[+] Experiment 1 (amsterdam01, uw01): Announcement"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_amsterdam01_uw01.json -a -d
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
#echo "[+] Experiment 1 (amsterdam01, uw01): Withdrawal"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_amsterdam01_uw01.json
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800

##2) ['grnet01', 'uw01'], catchment: ~25/75
#echo "[+] Experiment 2 (grnet01, uw01): Announcement"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_grnet01_uw01.json -a -d
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
#echo "[+] Experiment 2 (grnet01, uw01): Withdrawal"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_grnet01_uw01.json
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800

#3) ['ufmg01', 'uw01'], catchment: ~20/80
echo "[+] Experiment 3 (ufmg01, uw01): Announcement"
/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_ufmg01_uw01.json -a -d
echo "[+] Safe waiting for 30 minutes..."
sleep 1800
echo "[+] Experiment 3 (ufmg01, uw01): Withdrawal"
/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_ufmg01_uw01.json
echo "[+] Safe waiting for 30 minutes..."
sleep 1800

##4) ['phoenix01', 'uw01'], catchment: ~15/85
#echo "[+] Experiment 4 (phoenix01, uw01): Announcement"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_phoenix01_uw01.json -a -d
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
#echo "[+] Experiment 4 (phoenix01, uw01): Withdrawal"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_phoenix01_uw01.json
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800

##5) ['grnet01', 'seattle01'], catchment: ~15/85
#echo "[+] Experiment 5 (grnet01, seattle01): Announcement"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_grnet01_seattle01.json -a -d
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
#echo "[+] Experiment 5 (grnet01, seattle01): Withdrawal"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_grnet01_seattle01.json
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800

#6) ['seattle01', 'ufmg01'], catchment: ~10/90
echo "[+] Experiment 6 (seattle01, ufmg01): Announcement"
/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_seattle01_ufmg01.json -a -d
echo "[+] Safe waiting for 30 minutes..."
sleep 1800
echo "[+] Experiment 6 (seattle01, ufmg01): Withdrawal"
/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_seattle01_ufmg01.json
echo "[+] Safe waiting for 30 minutes..."
sleep 1800

##7) ['seattle01', 'uw01'], , catchment: ~10/90
#echo "[+] Experiment 7 (seattle01, uw01): Announcement"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_announcements_jsons/announce_seattle01_uw01.json -a -d
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
#echo "[+] Experiment 7 (seattle01, uw01): Withdrawal"
#/usr/bin/python3 run_peering_exp.py -e mux_pair_withdrawals_jsons/withdraw_seattle01_uw01.json
#echo "[+] Safe waiting for 30 minutes..."
#sleep 1800
