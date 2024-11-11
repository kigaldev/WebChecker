# Crear nuevo archivo: src/utils/reports.py

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import pandas as pd

class ReportGenerator:
    """Genera reportes y visualizaciones de los datos de verificación."""
    
    def __init__(self, checker):
        self.checker = checker
    
    def generate_uptime_report(self, url: str, days: int = 7) -> dict:
        """Genera un reporte de uptime para los últimos N días."""
        history = self.checker.get_history(url)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filtrar registros por fecha
        relevant_history = [
            check for check in history
            if start_date <= check['timestamp'] <= end_date
        ]
        
        total_checks = len(relevant_history)
        successful_checks = sum(
            1 for check in relevant_history
            if check['status_code'] == 200
        )
        
        return {
            'url': url,
            'period': f'{days} días',
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'uptime_percentage': (successful_checks / total_checks * 100) if total_checks > 0 else 0,
            'average_response_time': sum(
                (check['end_time'] - check['start_time']).total_seconds() * 1000
                for check in relevant_history
            ) / total_checks if total_checks > 0 else 0
        }
    
    def plot_response_times(self, url: str, output_file: str = None):
        """Genera un gráfico de tiempos de respuesta."""
        history = self.checker.get_history(url)
        
        dates = [check['timestamp'] for check in history]
        response_times = [
            (check['end_time'] - check['start_time']).total_seconds() * 1000
            for check in history
        ]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, response_times, marker='o')
        plt.title(f'Tiempos de respuesta para {url}')
        plt.xlabel('Fecha/Hora')
        plt.ylabel('Tiempo de respuesta (ms)')
        plt.grid(True)
        plt.xticks(rotation=45)
        
        if output_file:
            plt.savefig(output_file)
        else:
            plt.show()
    
    def export_to_excel(self, filename: str):
        """Exporta todos los datos a un archivo Excel."""
        workbook = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # Hoja de resumen
        summary_data = []
        for url in self.checker._history.keys():
            stats = self.checker.get_statistics(url)
            summary_data.append({
                'URL': url,
                'Total Checks': stats['total_checks'],
                'Success Rate': f"{stats['success_rate']:.2f}%",
                'Avg Response Time': f"{stats['avg_response_time']:.2f}ms"
            })
        
        pd.DataFrame(summary_data).to_excel(
            workbook,
            sheet_name='Summary',
            index=False
        )
        
        # Hoja detallada por URL
        for url in self.checker._history.keys():
            history = self.checker.get_history(url)
            df = pd.DataFrame([{
                'Timestamp': check['timestamp'],
                'Status Code': check['status_code'],
                'Response Time': (check['end_time'] - check['start_time']).total_seconds() * 1000
            } for check in history])
            
            df.to_excel(workbook, sheet_name=url[:31], index=False)
        
        workbook.close()