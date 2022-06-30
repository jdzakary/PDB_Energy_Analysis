def load_text(folder_name: str, file_name: str) -> str:
    with open(f'text/{folder_name}/{file_name}.txt', 'r') as file:
        data = file.read()
    return data.strip('\n')
