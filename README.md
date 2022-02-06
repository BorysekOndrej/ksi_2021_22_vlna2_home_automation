# Ukázkový kód pro KSI - Web server pro chytrou domácnost

Ukázkový kód pro úlohu [Web server pro chytrou domácnost](https://ksi.fi.muni.cz/ulohy/451) z [Korespondečního semináře z informatiky](https://ksi.fi.muni.cz/).

Při prvním běhu

- `python -m pip install -U -r requirements.txt`
- `python create_devices.py`
- zkopíruj `.env.dist` do `.env.` a uprav `.env` aby obsahoval náhodný secret.

Pak už normálně můžeš spustit Flask v app.py
