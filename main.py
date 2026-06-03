#!/usr/bin/env python3
# Created by null7

import os
import sys
import json
import requests
from datetime import datetime
from colorama import init, Fore, Back, Style
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import hashlib

init(autoreset=True)

BANNER = f"""
{Fore.RED}{Style.BRIGHT}
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗    ███████╗██╗   ██╗███████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝    ██╔════╝╚██╗ ██╔╝██╔════╝
██║  ███╗███████║██║   ██║███████╗   ██║       █████╗   ╚████╔╝ █████╗  
██║   ██║██╔══██║██║   ██║╚════██║   ██║       ██╔══╝    ╚██╔╝  ██╔══╝  
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║       ███████╗   ██║   ███████╗
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝       ╚══════╝   ╚═╝   ╚══════╝
{Fore.RED}[ {Fore.WHITE}GHOST EYE {Fore.RED}] {Fore.YELLOW}Deep Image Forensic & Metadata Extractor
{Fore.RED}[ {Fore.WHITE}Created by null7 {Fore.RED}] {Fore.YELLOW}Every pixel tells a story.
"""

def dms_to_decimal(dms, ref):
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes)/60.0 + float(seconds)/3600.0
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_exif_data(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if not exif_data:
            return None, None, None, False
        
        exif_info = {}
        gps_info = {}
        gps_active = False
        
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            exif_info[tag_name] = str(value)
        
        gps_data = exif_data.get(34853, {})
        lat = None
        lon = None
        
        if gps_data:
            gps_active = True
            for tag_id, value in gps_data.items():
                tag_name = GPSTAGS.get(tag_id, tag_id)
                gps_info[tag_name] = str(value)
            
            try:
                if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                    lat = dms_to_decimal(gps_data['GPSLatitude'], gps_data.get('GPSLatitudeRef', 'N'))
                    lon = dms_to_decimal(gps_data['GPSLongitude'], gps_data.get('GPSLongitudeRef', 'E'))
            except:
                pass
        
        return exif_info, gps_info, (lat, lon), gps_active
    
    except Exception as e:
        return None, None, None, False

def extract_file_info(image_path):
    file_info = {}
    
    stat = os.stat(image_path)
    file_info['File Name'] = os.path.basename(image_path)
    file_info['File Path'] = os.path.abspath(image_path)
    file_info['File Size'] = f"{stat.st_size / 1024:.2f} KB ({stat.st_size} bytes)"
    file_info['Created'] = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
    file_info['Modified'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    file_info['Accessed'] = datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')
    
    file_hash = hashlib.md5()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            file_hash.update(chunk)
    file_info['MD5 Hash'] = file_hash.hexdigest()
    
    sha256_hash = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    file_info['SHA-256 Hash'] = sha256_hash.hexdigest()
    
    try:
        img = Image.open(image_path)
        file_info['Format'] = img.format
        file_info['Mode'] = img.mode
        file_info['Dimensions'] = f"{img.width} x {img.height} pixels"
        file_info['Aspect Ratio'] = f"{img.width/img.height:.2f}"
        
        if img.mode == 'RGB':
            try:
                pixels = list(img.get_flattened_data())
            except AttributeError:
                pixels = list(img.getdata())
            r_avg = sum(p[0] for p in pixels) / len(pixels)
            g_avg = sum(p[1] for p in pixels) / len(pixels)
            b_avg = sum(p[2] for p in pixels) / len(pixels)
            file_info['Avg Color (RGB)'] = f"R:{r_avg:.0f} G:{g_avg:.0f} B:{b_avg:.0f}"
            
            brightness = (r_avg * 299 + g_avg * 587 + b_avg * 114) / 1000
            file_info['Brightness'] = f"{brightness:.1f}/255"
            
            if brightness > 127:
                file_info['Light/Dark'] = "Gambar Terang (Daylight)"
            else:
                file_info['Light/Dark'] = "Gambar Gelap (Low Light)"
        
        file_info['Color Depth'] = f"{img.bits * len(img.getbands())}-bit"
        file_info['DPI'] = str(img.info.get('dpi', 'Not available'))
        file_info['Compression'] = img.info.get('compression', 'Unknown')
        
    except Exception as e:
        file_info['Image Error'] = str(e)
    
    return file_info

def get_geolocation_info(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&addressdetails=1"
        headers = {'User-Agent': 'GhostEye/1.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        if 'address' in data:
            addr = data['address']
            location_info = {
                'Display Name': data.get('display_name', 'Unknown'),
                'Country': addr.get('country', 'N/A'),
                'Country Code': addr.get('country_code', 'N/A'),
                'State/Province': addr.get('state', addr.get('region', 'N/A')),
                'City': addr.get('city', addr.get('town', addr.get('village', 'N/A'))),
                'District': addr.get('district', addr.get('county', 'N/A')),
                'Postcode': addr.get('postcode', 'N/A'),
                'Road': addr.get('road', 'N/A'),
                'Neighbourhood': addr.get('neighbourhood', addr.get('suburb', 'N/A')),
                'Amenity': addr.get('amenity', 'N/A'),
                'Maps Link': f"https://www.google.com/maps?q={lat},{lon}"
            }
            return location_info
    except:
        pass
    return None

def detect_photo_manipulation(file_info, exif_info):
    manipulation_score = 0
    flags = []
    
    if exif_info is None:
        manipulation_score += 20
        flags.append("Tidak ada metadata EXIF (kemungkinan dihapus)")
    else:
        if 'Software' in exif_info:
            software = exif_info['Software'].lower()
            if any(sw in software for sw in ['photoshop', 'lightroom', 'gimp', 'paint.net', 'adobe']):
                manipulation_score += 30
                flags.append(f"Diedit dengan: {exif_info['Software']}")
        
        if 'DateTimeOriginal' not in exif_info and 'DateTime' not in exif_info:
            manipulation_score += 10
            flags.append("Tidak ada timestamp original")
    
    return manipulation_score, flags

def display_results(file_info, exif_info, gps_info, coords, gps_active, location_info, manipulation_score, flags):
    print(Fore.RED + Style.BRIGHT + "\nHASIL ANALISIS GAMBAR" + Style.RESET_ALL)
    print(Fore.RED + "-" * 60)
    
    print(Fore.CYAN + Style.BRIGHT + "\nINFORMASI FILE" + Style.RESET_ALL)
    print(Fore.RED + "-" * 60)
    file_fields = [
        'File Name', 'File Size', 'Format', 'Mode', 'Dimensions', 
        'Aspect Ratio', 'Color Depth', 'DPI', 'Compression',
        'Avg Color (RGB)', 'Brightness', 'Light/Dark',
        'Created', 'Modified', 'Accessed',
        'MD5 Hash', 'SHA-256 Hash'
    ]
    for field in file_fields:
        if field in file_info:
            print(f"{Fore.RED}{field:20}{Fore.WHITE}: {Fore.GREEN}{file_info[field]}")
    
    print(Fore.CYAN + Style.BRIGHT + "\nSTATUS GPS" + Style.RESET_ALL)
    print(Fore.RED + "-" * 60)
    if gps_active:
        print(f"{Fore.RED}{'GPS Status':20}{Fore.WHITE}: {Fore.GREEN}AKTIF - Target menyalakan GPS saat mengambil foto")
    else:
        print(f"{Fore.RED}{'GPS Status':20}{Fore.WHITE}: {Fore.YELLOW}TIDAK AKTIF - GPS dimatikan atau tidak tersedia di perangkat")
    
    if exif_info:
        print(Fore.CYAN + Style.BRIGHT + "\nMETADATA EXIF" + Style.RESET_ALL)
        print(Fore.RED + "-" * 60)
        exif_important = [
            'Make', 'Model', 'Software', 'DateTimeOriginal', 
            'DateTime', 'ExposureTime', 'FNumber', 'ISOSpeedRatings',
            'FocalLength', 'Flash', 'WhiteBalance', 'LensModel'
        ]
        for field in exif_important:
            if field in exif_info:
                print(f"{Fore.RED}{field:20}{Fore.WHITE}: {Fore.GREEN}{exif_info[field]}")
        
        other_exif = {k: v for k, v in exif_info.items() if k not in exif_important}
        if other_exif:
            print(f"\n{Fore.YELLOW}Metadata Tambahan:{Style.RESET_ALL}")
            for k, v in list(other_exif.items())[:15]:
                if len(str(v)) < 100:
                    print(f"  {Fore.RED}{k:18}{Fore.WHITE}: {Fore.GREEN}{v}")
    
    if gps_info:
        print(Fore.CYAN + Style.BRIGHT + "\nKOORDINAT GPS MENTAH" + Style.RESET_ALL)
        print(Fore.RED + "-" * 60)
        for k, v in gps_info.items():
            print(f"{Fore.RED}{k:20}{Fore.WHITE}: {Fore.GREEN}{v}")
    
    if coords and coords[0] and coords[1]:
        lat, lon = coords
        print(Fore.CYAN + Style.BRIGHT + "\nLOKASI DITEMUKAN" + Style.RESET_ALL)
        print(Fore.RED + "-" * 60)
        print(f"{Fore.RED}{'Coordinates':20}{Fore.WHITE}: {Fore.GREEN}{lat}, {lon}")
        print(f"{Fore.RED}{'Google Maps':20}{Fore.WHITE}: {Fore.CYAN}https://www.google.com/maps?q={lat},{lon}")
        print(f"{Fore.RED}{'Street View':20}{Fore.WHITE}: {Fore.CYAN}https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}")
        
        if location_info:
            loc_fields = [
                'Country', 'Country Code', 'State/Province', 'City',
                'District', 'Postcode', 'Road', 'Neighbourhood',
                'Amenity', 'Display Name'
            ]
            for field in loc_fields:
                if field in location_info:
                    print(f"{Fore.RED}{field:20}{Fore.WHITE}: {Fore.GREEN}{location_info[field]}")
    elif gps_active:
        print(f"\n{Fore.YELLOW}Koordinat GPS ditemukan tapi tidak bisa dikonversi ke lokasi.{Style.RESET_ALL}")
    
    print(Fore.CYAN + Style.BRIGHT + "\nANALISIS FORENSIK" + Style.RESET_ALL)
    print(Fore.RED + "-" * 60)
    print(f"{Fore.RED}{'Manipulation Score':20}{Fore.WHITE}: {Fore.YELLOW}{manipulation_score}/100")
    if manipulation_score < 20:
        print(f"{Fore.RED}{'Verdict':20}{Fore.WHITE}: {Fore.GREEN}Kemungkinan Original")
    elif manipulation_score < 50:
        print(f"{Fore.RED}{'Verdict':20}{Fore.WHITE}: {Fore.YELLOW}Kemungkinan Diedit")
    else:
        print(f"{Fore.RED}{'Verdict':20}{Fore.WHITE}: {Fore.RED}Sangat Mungkin Dimanipulasi")
    
    if flags:
        print(f"\n{Fore.YELLOW}Flags Terdeteksi:{Style.RESET_ALL}")
        for flag in flags:
            print(f"  {Fore.RED}- {Fore.WHITE}{flag}")
    
    print(Fore.RED + "\n" + "-" * 60)
    print(Fore.RED + "Forensik selesai. Setiap piksel telah diperiksa.\n")

if __name__ == "__main__":
    print(BANNER)
    
    if len(sys.argv) > 1:
        image_name = sys.argv[1]
    else:
        print(Fore.YELLOW + "[?] Masukkan nama gambar target" + Fore.WHITE)
        image_name = input(Fore.RED + "    > " + Fore.WHITE).strip().strip('"').strip("'")
    
    if not image_name:
        print(Fore.RED + "[!] Tidak ada nama gambar yang dimasukkan.")
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, image_name)
    
    if not os.path.exists(image_path):
        print(Fore.RED + f"[!] File '{image_name}' tidak ditemukan di folder script.")
        print(Fore.RED + f"[!] Letakkan gambar di folder yang sama dengan script ini.")
        sys.exit(1)
    
    print(Fore.YELLOW + f"\n[*] Menganalisis gambar: {image_name}")
    print(Fore.YELLOW + "[*] Mengekstrak metadata...")
    print(Fore.YELLOW + "[*] Membaca piksel...")
    print(Fore.YELLOW + "[*] Mencari jejak digital...")
    print(Fore.YELLOW + "[*] Memeriksa status GPS...\n")
    
    file_info = extract_file_info(image_path)
    exif_info, gps_info, coords, gps_active = extract_exif_data(image_path)
    location_info = None
    
    if coords and coords[0] and coords[1]:
        print(Fore.GREEN + "[+] GPS AKTIF! Koordinat ditemukan, mencari lokasi...")
        location_info = get_geolocation_info(coords[0], coords[1])
    elif gps_active:
        print(Fore.YELLOW + "[!] GPS aktif tapi koordinat tidak valid.")
    else:
        print(Fore.YELLOW + "[!] GPS tidak aktif. Target mematikan lokasi saat foto.")
    
    manipulation_score, flags = detect_photo_manipulation(file_info, exif_info)
    
    display_results(file_info, exif_info, gps_info, coords, gps_active, location_info, manipulation_score, flags)
