import streamlit_authenticator as stauth

# Contraseñas claras
passwords = [
    "Rimec2019egiDios", 
    "Rimec2019G0126", 
    "Rimec2019rmc"
]

# Sintaxis compatible con 0.3.3
hashed_passwords = stauth.Hasher(passwords).generate()

# Imprimir los hashes
print(hashed_passwords)