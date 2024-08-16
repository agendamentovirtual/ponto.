from flask import Flask, render_template, request, jsonify
from scapy.all import ARP, Ether, srp
from flask_cors import CORS
app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('ponto.html')


CORS(app)  # Adiciona suporte a CORS

# Localização do trabalho
TRABALHO_LAT = -13.4414336
TRABALHO_LON = -49.1520000

# Tolerância em metros para a localização
TOLERANCIA_METROS = 50

# MAC Address do roteador correto
ROUTER_MAC_ADDRESS = 'D8:36:5F:F6:66:C1'

# IP do roteador (assumindo que está na rede local)
ROUTER_IP = '192.168.1.1'


def calcular_distancia(lat1, lon1, lat2, lon2):
    from geopy.distance import geodesic
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def get_router_mac(ip):
    arp_request = ARP(pdst=ip)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    if answered_list:
        return answered_list[0][1].hwsrc
    return None


@app.route('/check-in', methods=['POST'])
def check_in():
    data = request.json
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')

    if user_lat is None or user_lon is None:
        return jsonify({"message": "Localização não fornecida"}), 400

    # Verifica se a pessoa está na localização correta
    distancia = calcular_distancia(user_lat, user_lon, TRABALHO_LAT, TRABALHO_LON)

    if distancia > TOLERANCIA_METROS:
        return jsonify({"message": "Você não está no local de trabalho"}), 403

    # Obtém o MAC Address do roteador e verifica se é o correto
    router_mac = get_router_mac(ROUTER_IP)

    if router_mac is None:
        return jsonify({"message": "Não foi possível verificar o roteador"}), 500

    # Comparação de MAC address
    if router_mac.lower() == ROUTER_MAC_ADDRESS.lower():
        print("Ponto batido da mesma rede (MAC address correto):", router_mac)
        return jsonify({"message": "Ponto registrado com sucesso!"}), 200
    else:
        print("Ponto batido de uma rede diferente (MAC address incorreto):", router_mac)
        return jsonify({"message": "Você não está conectado ao roteador correto"}), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)