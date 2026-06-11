from modules.csv_reader import load_roles
from config.settings import INPUT_CSV

roles = load_roles(
    INPUT_CSV
)

print(roles)