import os
import re

PYTHON_FILES = [
    'services/data_fetcher.py',
    'views/market_health.py',
    'views/stock_analysis.py',
    'weinstein.py',
    'seaf_model.py',
    'options_flow.py',
    'canslim.py',
    'asbury_metrics.py',
    'gamma_profile.py',
    'congress_tracker.py',
    'fundamental_metrics.py',
    'macro_analysis.py',
    'screener_engine.py',
    'power_gauge.py'
]

IMPORT_STMT = "from services.logger import setup_logger\nlogger = setup_logger(__name__)\n"

for file_path in PYTHON_FILES:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, 'r') as f:
        content = f.read()
        
    if 'print(' not in content:
        continue
        
    # Check if we should ignore (maybe only print is in __main__)
    # Let's just do a simple replacement for now.
    
    # Add import if not present
    if 'setup_logger' not in content:
        # Insert after the last import
        import_match = list(re.finditer(r'^import [^\n]+|^from [^\n]+', content, flags=re.MULTILINE))
        if import_match:
            last_import = import_match[-1]
            insert_pos = last_import.end() + 1
            content = content[:insert_pos] + IMPORT_STMT + content[insert_pos:]
        else:
            content = IMPORT_STMT + content
            
    # Replace print( with logger.info( or error( if it looks like an error
    def replace_print(match):
        stmt = match.group(0)
        if 'error' in stmt.lower() or 'exception' in stmt.lower():
            return stmt.replace('print(', 'logger.error(')
        return stmt.replace('print(', 'logger.info(')
        
    content = re.sub(r'^(\s*)print\(', replace_print, content, flags=re.MULTILINE)
    
    with open(file_path, 'w') as f:
        f.write(content)
        
print("Prints replaced.")
