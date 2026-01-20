import markdown
import os
import re
import yaml
import json
import shutil
from string import Template


def parse_front_matter(markdown_text):
    """
    Parses YAML front matter and returns metadata and content.
    """
    front_matter_pattern = r'\A---\s*$(.*?)^\s*---\s*$(.*)'
    match = re.search(front_matter_pattern, markdown_text, re.MULTILINE | re.DOTALL)

    if match:
        front_matter_str, content = match.groups()
        try:
            metadata = yaml.safe_load(front_matter_str) or {}
            return metadata, content.strip()
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse YAML front matter. {e}")
            return {}, markdown_text
    return {}, markdown_text


def create_missing_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: '{path}'")


def copy_static_assets(static_src_dirs, output_dir):
    """
    Copies a static asset directory to the output directory.
    """

    print("\n--- Copying Static Assets ---")

    for static_src_dir in static_src_dirs:

        if not os.path.exists(static_src_dir):
            print(f"Warning: Static source directory '{static_src_dir}' not found. Skipping copy.")
            return

        output_static_path = os.path.join(output_dir, os.path.basename(static_src_dir))

        if os.path.exists(output_static_path):
            shutil.rmtree(output_static_path)

        shutil.copytree(static_src_dir, output_static_path)
        print(f"Copied '{static_src_dir}' -> '{output_static_path}'")


def generate_navigation_links(input_dir, navigation_links_list):
    # Generate Navigation Links
    for filename in os.listdir(input_dir):
        if not filename.endswith(('.md', '.markdown')):
            continue

        input_file_path = os.path.join(input_dir, filename)
        base_filename = os.path.splitext(filename)[0]
        output_html_path = os.path.join(base_filename + '.html')

        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        metadata, markdown_content = parse_front_matter(raw_text)
        page_name = metadata['title']
        if metadata['navmenu'] == True:
            page_order = metadata['navorder']
            navigation_links_list.append({
                'html_file': output_html_path,
                'page_name': page_name,
                'page_order': page_order
            })
    navigation_links_list.sort(key=lambda item: item['page_order'])
    return navigation_links_list


def generate_containers_markdown(containers_path):

    if not os.path.isdir(containers_path):
        print(f"Error: Containers directory '{containers_path}' not found.")
        return

    print("\n--- Generating Containers HTML ---")

    containers_markdown = ''
    filter_groups = []
    filter_buttons = [f'\n\t\t\t\t<button class="filter-btn active" data-filter="all">All</button>']
    containers = []

    for filename in os.listdir(containers_path):
        if not filename.endswith(('.md', '.markdown')):
            continue

        input_file_path = os.path.join(containers_path, filename)

        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        metadata, markdown_content = parse_front_matter(raw_text)

        container_groups = metadata['containergroups']
        container_image = metadata['containerimage']
        container_alttext = metadata['containeralttext']
        container_link = metadata['containerlink']
        container_title = metadata['containertitle']

        for container_group in container_groups:
            if container_group not in filter_groups:
                filter_groups.append(container_group)

        container_groups_dq = json.dumps(container_groups)
        containers.append(f"\n\t\t\t\t<div class='item' data-groups='{container_groups_dq}'>\n\t\t\t\t\t<a href='{container_link}'>\n\t\t\t\t\t\t<img src='{container_image}' alt='{container_alttext}'  class='item_img'>\n\t\t\t\t\t\t<div class='item_overlay'>\n\t\t\t\t\t\t\t<div class='item_text'>\n\t\t\t\t\t\t\t\t<h3>{container_title}</h3>\n\t\t\t\t\t\t\t\t<p>{container_title}</p>\n\t\t\t\t\t\t\t</div>\n\t\t\t\t\t\t</div>\n\t\t\t\t\t</a>\n\t\t\t\t</div>")

    filter_groups.sort()
    for filter_group in filter_groups:
        filter_buttons.append(f'\n\t\t\t\t<button class="filter-btn" data-filter="{filter_group}">{filter_group}</button>')

    containers_markdown = '\n\t\t\t<div class="filter-buttons">' + "".join(filter_buttons) + '\n\t\t\t</div>' + '\n\t\t\t<div class="items-container">' + "".join(containers) + '\n\t\t\t</div>'

    return containers_markdown


def generate_data(input_dir, json_dir, navigation_links_list, ref_prefix):
    """
    Processes Markdown files from input_dir, converts their content to
    HTML, and saves everything as structured JSON files in json_dir.
    """

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    create_missing_directory(json_dir)

    print("\n--- Generating Data from Markdown ---")

    navigation_links_list = generate_navigation_links(input_dir, navigation_links_list)

    for filename in os.listdir(input_dir):
        if os.path.isdir(os.path.join(input_dir, filename)):
            print(f"Subdirectory found: '{filename}'")
            generate_data(
                os.path.join(input_dir, filename),
                os.path.join(json_dir, filename),
                navigation_links_list,
                ref_prefix + '../'
            )

        if not filename.endswith(('.md', '.markdown')):
            continue

        input_file_path = os.path.join(input_dir, filename)
        base_filename = os.path.splitext(filename)[0]
        output_json_path = os.path.join(json_dir, base_filename + '.json')

        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        metadata, markdown_content = parse_front_matter(raw_text)
        html_content = markdown.markdown(markdown_content)

        # The final data object to be saved as JSON
        page_data = metadata
        page_data['page_markdown'] = html_content
        navigation_links = ''
        for navigation_link in navigation_links_list:
            href = navigation_link['html_file']
            page_name = navigation_link['page_name']
            a_class = f' class="active"' if page_name == page_data['title'] else ''
            navigation_links += f'\n\t\t\t\t\t\t<li><a href="{ref_prefix}{href}"{a_class}>{page_name}</a></li>'
        page_data['navigation_links'] = navigation_links

        if page_data['layout'] == 'containers':
            page_data['containers_markdown'] = generate_containers_markdown(
                input_dir + '/' + page_data['containerspath']
            )

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=4)
        print(f"Generated data for '{filename}' -> '{output_json_path}'")


def render_site(json_dir, template_dir, output_dir, ref_prefix):
    """
    Reads JSON data files, applies the corresponding template,
    and renders the final HTML files to the output_dir.
    """

    if not os.path.isdir(template_dir):
        print(f"Error: HTML Template directory '{template_dir}' not found.")
        return

    if not os.path.isdir(json_dir):
        print(f"Error: JSON data directory '{json_dir}' not found.")
        return

    create_missing_directory(output_dir)

    print("\n--- Rendering Site from JSON Data ---")
    for filename in os.listdir(json_dir):

        if os.path.isdir(os.path.join(json_dir, filename)):
            print(f"Subdirectory found: '{filename}'")
            render_site(
                os.path.join(json_dir, filename),
                template_dir,
                os.path.join(output_dir, filename),
                ref_prefix + '../'
            )

        if not filename.endswith('.json'):
            continue

        json_file_path = os.path.join(json_dir, filename)
        base_filename = os.path.splitext(filename)[0]
        output_html_path = os.path.join(output_dir, base_filename + '.html')

        with open(json_file_path, 'r', encoding='utf-8') as f:
            page_data = json.load(f)

        template_name = page_data.get('layout', 'page') + '.html'
        template_path = os.path.join(template_dir, template_name)

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = Template(f.read())
        except FileNotFoundError:
            print(f"Warning: Template '{template_name}' not found for '{filename}'. Skipping.")
            continue

        if 'title' not in page_data:
            page_data['title'] = 'Untitled'
        if 'page_markdown' not in page_data:
            page_data['page_markdown'] = ''
        page_data['ref_prefix'] = ref_prefix

        try:
            final_html = template.substitute(page_data)
        except KeyError as e:
            print(f"Warning: Missing key {e} in data for '{filename}'. Skipping.")
            continue

        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"Rendered '{filename}' -> '{output_html_path}'")

    # for dirname in os.listdir(json_dir):
    #         if os.path.isdir(os.path.join(path, name))]


def main():
    # The script is in 'src', so the project root is one level up.
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)

    # Define all source and destination directories based on the project root
    css_directory = os.path.join(project_root, '_data/assets/css')
    scripts_directory = os.path.join(project_root, '_data/assets/scripts')
    input_directory = os.path.join(project_root, '_data/pages')
    images_directory = os.path.join(project_root, '_data/pages/images')
    json_directory = os.path.join(project_root, '_data/working/page_json')
    template_directory = os.path.join(project_root, '_data/assets/templates')
    output_directory = os.path.join(project_root, 'docs')

    # Run all stages
    generate_data(input_directory, json_directory, [], './')
    render_site(json_directory, template_directory, output_directory, './')
    copy_static_assets([css_directory, scripts_directory, images_directory], output_directory)

    print("\nSite generation complete!")


if __name__ == '__main__':
    main()