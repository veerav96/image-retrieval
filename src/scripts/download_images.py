import os
import requests
import xml.etree.ElementTree as ET


def find_graphic_url_in_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    graphic_urls = []
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}  # Define the namespace mapping
    for figure in root.findall('.//tei:figure', ns):
        graphic = figure.find('./tei:graphic', ns)
        if graphic is not None:
            url = graphic.get('url')
            if url and url.startswith('https://digi.ub.uni-heidelberg.de/diglit'):
                graphic_urls.append(url)
    return graphic_urls


def download_image(url, save_path, xml_filename, log_file, success_count, failure_count):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        log_file.write(f'Downloaded {save_path}\n')
        success_count += 1
    else:
        log_file.write(f'Failed to download {url} for file {xml_filename}\n')
        failure_count += 1
    return success_count, failure_count


def process_xml_files(xml_folder, image_save_folder, log_file_path):
    success_count = 0
    failure_count = 0
    with open(log_file_path, 'w') as log_file:
        for root_dir, _, files in os.walk(xml_folder):
            for filename in files:
                if filename.endswith('.xml'):
                    xml_file_path = os.path.join(root_dir, filename)
                    graphic_urls = find_graphic_url_in_xml(xml_file_path)

                    relative_dir = os.path.relpath(root_dir, xml_folder)
                    save_dir = os.path.join(image_save_folder, relative_dir)

                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)

                    base_filename = os.path.splitext(filename)[0]

                    for url in graphic_urls:
                        url_parts = url.split('/')
                        image_name = url_parts[-1]
                        image_url = f'{url}/0001/_image'
                        save_path = os.path.join(save_dir, f'{base_filename}_{image_name}.jpg')
                        success_count, failure_count = download_image(
                            image_url, save_path, filename, log_file, success_count, failure_count
                        )

        log_file.write(f'\nTotal successful downloads: {success_count}\n')
        log_file.write(f'Total failed downloads: {failure_count}\n')


if __name__ == '__main__':
    xml_folder = 'data-master/HGV_meta_EpiDoc'
    image_save_folder = 'images'
    log_file_path = 'download_images.log'  # Path to the log file
    process_xml_files(xml_folder, image_save_folder, log_file_path)
