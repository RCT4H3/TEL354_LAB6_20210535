#!/usr/bin/env python3
"""
TEL354 - Laboratorio 6: Aplicación REST en Python 
Nombres: Roberto Carlos Tafur Herrera
Código: 20210535
"""

import yaml
import json
import requests
import sys
from typing import List, Dict, Optional

# Configuración del controlador Floodlight
FLOODLIGHT_HOST = "10.20.12.175"
FLOODLIGHT_PORT = 8080
FLOODLIGHT_URL = f"http://{FLOODLIGHT_HOST}:{FLOODLIGHT_PORT}"

class Alumno:
    """Clase para representar un alumno"""
    def __init__(self, nombre: str, codigo: str, mac: str):
        self.nombre = nombre
        self.codigo = codigo
        self.mac = mac.upper()  
    
    def __str__(self):
        return f"Alumno: {self.nombre} ({self.codigo}) - MAC: {self.mac}"
    
    def to_dict(self):
        return {
            'nombre': self.nombre,
            'codigo': self.codigo,
            'mac': self.mac
        }

class Servicio:
    """Clase para representar un servicio"""
    def __init__(self, nombre: str, protocolo: str, puerto: int):
        self.nombre = nombre
        self.protocolo = protocolo.upper()
        self.puerto = puerto
    
    def __str__(self):
        return f"{self.nombre} ({self.protocolo}:{self.puerto})"

class Servidor:
    """Clase para representar un servidor"""
    def __init__(self, nombre: str, ip: str, servicios: List[Dict] = None):
        self.nombre = nombre
        self.ip = ip
        self.servicios = []
        if servicios:
            for servicio in servicios:
                self.servicios.append(Servicio(
                    servicio['nombre'],
                    servicio['protocolo'],
                    servicio['puerto']
                ))
    
    def agregar_servicio(self, nombre: str, protocolo: str, puerto: int):
        """Agregar un servicio al servidor"""
        self.servicios.append(Servicio(nombre, protocolo, puerto))
    
    def obtener_servicio(self, nombre: str) -> Optional[Servicio]:
        """Obtener un servicio por nombre"""
        for servicio in self.servicios:
            if servicio.nombre == nombre:
                return servicio
        return None
    
    def __str__(self):
        return f"Servidor: {self.nombre} ({self.ip})"
    
    def to_dict(self):
        return {
            'nombre': self.nombre,
            'ip': self.ip,
            'servicios': [
                {
                    'nombre': s.nombre,
                    'protocolo': s.protocolo,
                    'puerto': s.puerto
                } for s in self.servicios
            ]
        }

class Curso:
    """Clase para representar un curso"""
    def __init__(self, codigo: str, nombre: str, estado: str = "DICTANDO"):
        self.codigo = codigo
        self.nombre = nombre
        self.estado = estado
        self.alumnos = []  # Lista de códigos de alumnos
        self.servidores = []  # Lista de configuraciones de servidor
    
    def agregar_alumno(self, codigo_alumno: str):
        """Agregar un alumno al curso"""
        if codigo_alumno not in self.alumnos:
            self.alumnos.append(codigo_alumno)
    
    def remover_alumno(self, codigo_alumno: str):
        """Remover un alumno del curso"""
        if codigo_alumno in self.alumnos:
            self.alumnos.remove(codigo_alumno)
    
    def agregar_servidor(self, nombre_servidor: str, servicios_permitidos: List[str]):
        """Agregar un servidor con servicios permitidos"""
        self.servidores.append({
            'nombre': nombre_servidor,
            'servicios_permitidos': servicios_permitidos
        })
    
    def __str__(self):
        return f"Curso: {self.codigo} - {self.nombre} ({self.estado})"
    
    def to_dict(self):
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'estado': self.estado,
            'alumnos': self.alumnos,
            'servidores': self.servidores
        }

class Conexion:
    """Clase para representar una conexión activa"""
    def __init__(self, handler: str, alumno_mac: str, servidor_ip: str, servicio: str):
        self.handler = handler
        self.alumno_mac = alumno_mac
        self.servidor_ip = servidor_ip
        self.servicio = servicio
        self.flow_entries = [] 
    
    def __str__(self):
        return f"Conexión {self.handler}: {self.alumno_mac} -> {self.servidor_ip}:{self.servicio}"

class SDNApp:
    """Aplicación principal SDN"""
    def __init__(self):
        self.alumnos = {} 
        self.cursos = {}  
        self.servidores = {}
        self.conexiones = {} 
        self.connection_counter = 0
    
    def importar_yaml(self, filename: str):
        """Importar datos desde archivo YAML"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            # Importar alumnos
            if 'alumnos' in data:
                for alumno_data in data['alumnos']:
                    alumno = Alumno(
                        alumno_data['nombre'],
                        alumno_data['codigo'],
                        alumno_data['mac']
                    )
                    self.alumnos[alumno.codigo] = alumno
            
            # Importar servidores
            if 'servidores' in data:
                for servidor_data in data['servidores']:
                    servidor = Servidor(
                        servidor_data['nombre'],
                        servidor_data['ip'],
                        servidor_data.get('servicios', [])
                    )
                    self.servidores[servidor.nombre] = servidor
            
            # Importar cursos
            if 'cursos' in data:
                for curso_data in data['cursos']:
                    curso = Curso(
                        curso_data['codigo'],
                        curso_data['nombre'],
                        curso_data.get('estado', 'DICTANDO')
                    )
                    curso.alumnos = curso_data.get('alumnos', [])
                    curso.servidores = curso_data.get('servidores', [])
                    self.cursos[curso.codigo] = curso
            
            print(f"Datos importados exitosamente desde {filename}")
            
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {filename}")
        except yaml.YAMLError as e:
            print(f"Error al leer el archivo YAML: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
    
    def exportar_yaml(self, filename: str):
        """Exportar datos a archivo YAML"""
        try:
            data = {
                'alumnos': [alumno.to_dict() for alumno in self.alumnos.values()],
                'cursos': [curso.to_dict() for curso in self.cursos.values()],
                'servidores': [servidor.to_dict() for servidor in self.servidores.values()]
            }
            
            with open(filename, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
            
            print(f"Datos exportados exitosamente a {filename}")
            
        except Exception as e:
            print(f"Error al exportar: {e}")
    
    def get_attachment_point(self, mac: str) -> Optional[Dict]:
        """Obtener punto de conexión de un dispositivo por MAC"""
        try:
            url = f"{FLOODLIGHT_URL}/wm/device/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                devices = response.json()
                for device in devices:
                    if 'mac' in device and device['mac'][0].upper() == mac.upper():
                        if 'attachmentPoint' in device and device['attachmentPoint']:
                            return device['attachmentPoint'][0]
            return None
            
        except requests.RequestException as e:
            print(f"Error al obtener attachment point: {e}")
            return None
    
    def get_route(self, src_dpid: str, src_port: int, dst_dpid: str, dst_port: int) -> Optional[List]:
        """Obtener ruta entre dos puntos"""
        try:
            url = f"{FLOODLIGHT_URL}/wm/routing/routes/fast/{src_dpid}/{src_port}/{dst_dpid}/{dst_port}/json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                route_data = response.json()
                if route_data:
                    return route_data[0]['route']
            return None
            
        except requests.RequestException as e:
            print(f"Error al obtener ruta: {e}")
            return None
    
    def build_route(self, alumno_mac: str, servidor_ip: str, servicio: Servicio) -> bool:
        """Construir e instalar rutas en la red"""
        try:
            # Obtener attachment points
            src_ap = self.get_attachment_point(alumno_mac)
            dst_ap = self.get_attachment_point("00:00:00:00:00:00")  # Buscar por IP en lugar de MAC
            
            if not src_ap or not dst_ap:
                print("Error: No se pudieron obtener los attachment points")
                return False
            
            # Obtener ruta
            route = self.get_route(
                src_ap['switch'], src_ap['port'],
                dst_ap['switch'], dst_ap['port']
            )
            
            if not route:
                print("Error: No se pudo calcular la ruta")
                return False
            
            # Instalar flows
            flow_entries = []
            
            # Flow para tráfico alumno hacia el server
            for hop in route:
                flow_entry = {
                    "switch": hop['switch'],
                    "name": f"flow_{self.connection_counter}_{hop['switch']}",
                    "cookie": "0",
                    "priority": "1000",
                    "active": "true",
                    "match": {
                        "dl_src": alumno_mac,
                        "dl_type": "0x0800",
                        "nw_dst": servidor_ip,
                        "nw_proto": "6" if servicio.protocolo == "TCP" else "17",
                        "tp_dst": str(servicio.puerto)
                    },
                    "actions": f"output={hop['port']}"
                }
                
                # Instalar flow
                url = f"{FLOODLIGHT_URL}/wm/staticflowpusher/json"
                response = requests.post(url, json=flow_entry, timeout=5)
                
                if response.status_code == 200:
                    flow_entries.append(flow_entry)
                else:
                    print(f"Error al instalar flow en switch {hop['switch']}")
                    return False
            
            # Flow para ARP OwO
            arp_flow = {
                "switch": src_ap['switch'],
                "name": f"arp_flow_{self.connection_counter}",
                "cookie": "0",
                "priority": "1000",
                "active": "true",
                "match": {
                    "dl_type": "0x0806"
                },
                "actions": "flood"
            }
            
            url = f"{FLOODLIGHT_URL}/wm/staticflowpusher/json"
            response = requests.post(url, json=arp_flow, timeout=5)
            
            if response.status_code == 200:
                flow_entries.append(arp_flow)
            
            return True
            
        except Exception as e:
            print(f"Error al construir ruta: {e}")
            return False
    
    def alumno_autorizado(self, codigo_alumno: str, nombre_servidor: str, nombre_servicio: str) -> bool:
        """Verificar si un alumno está autorizado para acceder a un servicio"""
        if codigo_alumno not in self.alumnos:
            return False
        
        if nombre_servidor not in self.servidores:
            return False
        
        servidor = self.servidores[nombre_servidor]
        servicio = servidor.obtener_servicio(nombre_servicio)
        if not servicio:
            return False
        
        # Verificar en todos los cursos
        for curso in self.cursos.values():
            if (curso.estado == "DICTANDO" and 
                codigo_alumno in curso.alumnos):
                
                # Verificar si el curso tiene acceso al servidor y servicio
                for servidor_config in curso.servidores:
                    if (servidor_config['nombre'] == nombre_servidor and
                        nombre_servicio in servidor_config['servicios_permitidos']):
                        return True
        
        return False
    
    def crear_conexion(self, codigo_alumno: str, nombre_servidor: str, nombre_servicio: str) -> Optional[str]:
        """Crear una conexión entre alumno y servidor"""
        if not self.alumno_autorizado(codigo_alumno, nombre_servidor, nombre_servicio):
            print(f"Error: El alumno {codigo_alumno} no está autorizado para acceder al servicio {nombre_servicio} en {nombre_servidor}")
            return None
        
        alumno = self.alumnos[codigo_alumno]
        servidor = self.servidores[nombre_servidor]
        servicio = servidor.obtener_servicio(nombre_servicio)
        
        if not servicio:
            print(f"Error: Servicio {nombre_servicio} no encontrado en {nombre_servidor}")
            return None
        
        # crear handler único
        handler = f"conn_{self.connection_counter}"
        self.connection_counter += 1
        
        # construir ruta
        if self.build_route(alumno.mac, servidor.ip, servicio):
            conexion = Conexion(handler, alumno.mac, servidor.ip, nombre_servicio)
            self.conexiones[handler] = conexion
            print(f"Conexión creada exitosamente: {handler}")
            return handler
        else:
            print("Error: No se pudo crear la conexión")
            return None
    
    def eliminar_conexion(self, handler: str) -> bool:
        """Eliminar una conexión"""
        if handler not in self.conexiones:
            print(f"Error: Conexión {handler} no encontrada")
            return False
        
        conexion = self.conexiones[handler]
        
        try:
            url = f"{FLOODLIGHT_URL}/wm/staticflowpusher/json"
            
            del self.conexiones[handler]
            print(f"Conexión {handler} eliminada exitosamente")
            return True
            
        except Exception as e:
            print(f"Error al eliminar conexión: {e}")
            return False
    
    def listar_alumnos(self, filtro_curso: str = None):
        """Listar alumnos, opcionalmente filtrados por curso"""
        if filtro_curso:
            if filtro_curso not in self.cursos:
                print(f"Error: Curso {filtro_curso} no encontrado")
                return
            
            curso = self.cursos[filtro_curso]
            print(f"\nAlumnos del curso {filtro_curso}:")
            for codigo in curso.alumnos:
                if codigo in self.alumnos:
                    print(f"- {self.alumnos[codigo]}")
        else:
            print("\nTodos los alumnos:")
            for alumno in self.alumnos.values():
                print(f"- {alumno}")
    
    def listar_cursos(self):
        """Listar todos los cursos"""
        print("\nCursos:")
        for curso in self.cursos.values():
            print(f"- {curso}")
    
    def mostrar_detalle_curso(self, codigo_curso: str):
        """Mostrar detalles de un curso"""
        if codigo_curso not in self.cursos:
            print(f"Error: Curso {codigo_curso} no encontrado")
            return
        
        curso = self.cursos[codigo_curso]
        print(f"\nDetalle del curso {codigo_curso}:")
        print(f"Nombre: {curso.nombre}")
        print(f"Estado: {curso.estado}")
        print(f"Alumnos matriculados: {len(curso.alumnos)}")
        for codigo in curso.alumnos:
            if codigo in self.alumnos:
                print(f"  - {self.alumnos[codigo].nombre} ({codigo})")
        print(f"Servidores con acceso: {len(curso.servidores)}")
        for servidor in curso.servidores:
            print(f"  - {servidor['nombre']}: {', '.join(servidor['servicios_permitidos'])}")
    
    def listar_servidores(self):
        """Listar todos los servidores"""
        print("\nServidores:")
        for servidor in self.servidores.values():
            print(f"- {servidor}")
    
    def mostrar_detalle_servidor(self, nombre_servidor: str):
        """Mostrar detalles de un servidor"""
        if nombre_servidor not in self.servidores:
            print(f"Error: Servidor {nombre_servidor} no encontrado")
            return
        
        servidor = self.servidores[nombre_servidor]
        print(f"\nDetalle del servidor {nombre_servidor}:")
        print(f"IP: {servidor.ip}")
        print(f"Servicios disponibles:")
        for servicio in servidor.servicios:
            print(f"  - {servicio}")
    
    def listar_conexiones(self):
        """Listar conexiones activas"""
        print("\nConexiones activas:")
        for conexion in self.conexiones.values():
            print(f"- {conexion}")
    
    def agregar_alumno(self, nombre: str, codigo: str, mac: str):
        """Agregar un nuevo alumno"""
        if codigo in self.alumnos:
            print(f"Error: Ya existe un alumno con código {codigo}")
            return
        
        alumno = Alumno(nombre, codigo, mac)
        self.alumnos[codigo] = alumno
        print(f"Alumno agregado: {alumno}")
    
    def agregar_alumno_a_curso(self, codigo_alumno: str, codigo_curso: str):
        """Agregar un alumno a un curso"""
        if codigo_alumno not in self.alumnos:
            print(f"Error: Alumno {codigo_alumno} no encontrado")
            return
        
        if codigo_curso not in self.cursos:
            print(f"Error: Curso {codigo_curso} no encontrado")
            return
        
        self.cursos[codigo_curso].agregar_alumno(codigo_alumno)
        print(f"Alumno {codigo_alumno} agregado al curso {codigo_curso}")
    
    def listar_cursos_con_servicio(self, nombre_servidor: str, nombre_servicio: str):
        """Listar cursos que tienen acceso a un servicio específico"""
        cursos_con_acceso = []
        
        for curso in self.cursos.values():
            if curso.estado == "DICTANDO":
                for servidor_config in curso.servidores:
                    if (servidor_config['nombre'] == nombre_servidor and
                        nombre_servicio in servidor_config['servicios_permitidos']):
                        cursos_con_acceso.append(curso)
                        break
        
        print(f"\nCursos con acceso al servicio {nombre_servicio} en {nombre_servidor}:")
        for curso in cursos_con_acceso:
            print(f"- {curso}")
    
    def menu(self):
        """Menú principal"""
        while True:
            print("\n" + "#"*50)
            print("Network Policy Manager de la UPSM")
            print("#"*50)
            print("1) Importar")
            print("2) Exportar")
            print("3) Cursos")
            print("4) Alumnos")
            print("5) Servidores")
            print("6) Políticas")
            print("7) Conexiones")
            print("8) Salir")
            print("#"*50)
            
            try:
                opcion = input("Seleccione una opción: ").strip()
                
                if opcion == '8':
                    print("Adiós, kiss kiss!")
                    break
                elif opcion == '1':
                    self.menu_importar()
                elif opcion == '2':
                    self.menu_exportar()
                elif opcion == '3':
                    self.menu_cursos()
                elif opcion == '4':
                    self.menu_alumnos()
                elif opcion == '5':
                    self.menu_servidores()
                elif opcion == '6':
                    self.menu_politicas()
                elif opcion == '7':
                    self.menu_conexiones()
                else:
                    print("Opción no válida. Intente nuevamente.")
                    
            except KeyboardInterrupt:
                print("\n¡Hasta luego!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def menu_importar(self):
        """Submenú para importar"""
        filename = input("Ingrese el nombre del archivo YAML: ").strip()
        if filename:
            self.importar_yaml(filename)
    
    def menu_exportar(self):
        """Submenú para exportar"""
        filename = input("Ingrese el nombre del archivo YAML: ").strip()
        if filename:
            self.exportar_yaml(filename)
    
    def menu_cursos(self):
        """Submenú para cursos"""
        while True:
            print("\n--- GESTIÓN DE CURSOS ---")
            print("1) Listar cursos")
            print("2) Mostrar detalle de curso")
            print("3) Actualizar curso (agregar/eliminar alumno)")
            print("0) Volver al menú principal")
            
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                break
            elif opcion == '1':
                self.listar_cursos()
            elif opcion == '2':
                codigo = input("Ingrese el código del curso: ").strip()
                self.mostrar_detalle_curso(codigo)
            elif opcion == '3':
                codigo_curso = input("Ingrese el código del curso: ").strip()
                codigo_alumno = input("Ingrese el código del alumno: ").strip()
                accion = input("¿Agregar o eliminar? (a/e): ").strip().lower()
                
                if accion == 'a':
                    self.agregar_alumno_a_curso(codigo_alumno, codigo_curso)
                elif accion == 'e':
                    if codigo_curso in self.cursos:
                        self.cursos[codigo_curso].remover_alumno(codigo_alumno)
                        print(f"Alumno {codigo_alumno} removido del curso {codigo_curso}")
            else:
                print("Opción no válida")
    
    def menu_alumnos(self):
        """Submenú para alumnos"""
        while True:
            print("\n--- GESTIÓN DE ALUMNOS ---")
            print("1) Listar todos los alumnos")
            print("2) Listar alumnos por curso")
            print("3) Mostrar detalle de alumno")
            print("4) Agregar alumno")
            print("0) Volver al menú principal")
            
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                break
            elif opcion == '1':
                self.listar_alumnos()
            elif opcion == '2':
                curso = input("Ingrese el código del curso: ").strip()
                self.listar_alumnos(curso)
            elif opcion == '3':
                codigo = input("Ingrese el código del alumno: ").strip()
                if codigo in self.alumnos:
                    print(f"\nDetalle del alumno:")
                    print(self.alumnos[codigo])
                else:
                    print("Alumno no encontrado")
            elif opcion == '4':
                nombre = input("Ingrese el nombre del alumno: ").strip()
                codigo = input("Ingrese el código del alumno: ").strip()
                mac = input("Ingrese la MAC del alumno: ").strip()
                self.agregar_alumno(nombre, codigo, mac)
            else:
                print("Opción no válida")
    
    def menu_servidores(self):
        """Submenú para servidores"""
        while True:
            print("\n--- GESTIÓN DE SERVIDORES ---")
            print("1) Listar servidores")
            print("2) Mostrar detalle de servidor")
            print("0) Volver al menú principal")
            
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                break
            elif opcion == '1':
                self.listar_servidores()
            elif opcion == '2':
                nombre = input("Ingrese el nombre del servidor: ").strip()
                self.mostrar_detalle_servidor(nombre)
            else:
                print("Opción no válida")
    
    def menu_politicas(self):
        """Submenú para políticas"""
        while True:
            print("\n--- GESTIÓN DE POLÍTICAS ---")
            print("1) Listar cursos con acceso a servicio")
            print("0) Volver al menú principal")
            
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                break
            elif opcion == '1':
                servidor = input("Ingrese el nombre del servidor: ").strip()
                servicio = input("Ingrese el nombre del servicio: ").strip()
                self.listar_cursos_con_servicio(servidor, servicio)
            else:
                print("Opción no válida")
    
    def menu_conexiones(self):
        """Submenú para conexiones"""
        while True:
            print("\n--- GESTIÓN DE CONEXIONES ---")
            print("1) Crear conexión")
            print("2) Listar conexiones")
            print("3) Eliminar conexión")
            print("0) Volver al menú principal")
            
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                break
            elif opcion == '1':
                alumno = input("Ingrese el código del alumno: ").strip()
                servidor = input("Ingrese el nombre del servidor: ").strip()
                servicio = input("Ingrese el nombre del servicio: ").strip()
                self.crear_conexion(alumno, servidor, servicio)
            elif opcion == '2':
                self.listar_conexiones()
            elif opcion == '3':
                handler = input("Ingrese el handler de la conexión: ").strip()
                self.eliminar_conexion(handler)
            else:
                print("Opción no válida")

def main():
    """Función principal"""
    app = SDNApp()
    
    try:
        app.importar_yaml("datos.yaml")
    except:
        print("No se encontró archivo de configuración inicial")
    
    app.menu()

if __name__ == "__main__":
    main()