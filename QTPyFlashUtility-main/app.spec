# app.spec

block_cipher = None

a = Analysis(['TelosAirSAMDBoardFlashGUI/__main__.py'],
             pathex=['./'],
             binaries=[],
             datas=[('./TelosAirSAMDBoardFlashGUI/util/device_binaries/*', 'device_binaries'), ("./TelosAirSAMDBoardFlashGUI/util/bossac_binaries/*", "bossac_binaries")],
             hiddenimports=["pywintypes", "tkinter"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=False,
          name='TelosAirQTPyFlashUtil',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False
           )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='App')
