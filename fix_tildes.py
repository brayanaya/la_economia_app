ï»¿import os

print('Iniciando rastreo de tildes con Python...')
for root, dirs, files in os.walk('.'):
    # Ignorar carpetas pesadas
    if '.venv' in root or '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.env') or file == 'alembic.ini':
            path = os.path.join(root, file)
            try:
                # Leer forzando la codificacion antigua que causa el problema
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
                # Si encuentra la tilde o el carÃ¡cter corrupto, lo aniquila
                if 'o' in content or 'EconomÃ­a' in content or 'ÃÂ³' in content:
                    content = content.replace('EconomÃ­a', 'Economia').replace('economÃ­a', 'economia').replace('o', 'o').replace('ÃÂ³', 'o')
                    # Guardar como UTF-8 puro
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'-> Desinfectado: {path}')
            except:
                pass
print('Â¡Limpieza completada!')
