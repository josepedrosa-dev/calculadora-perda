import unittest

from pdf_parser import extrair_dados_pdf_text, montar_df_a_partir_pdf, to_float_br


class TestPdfParser(unittest.TestCase):
    def test_to_float_br_formatos_mistos(self):
        self.assertEqual(to_float_br("1.234,56"), 1234.56)
        self.assertEqual(to_float_br("1,234.56"), 1234.56)
        self.assertEqual(to_float_br("50,065"), 50065.0)
        self.assertEqual(to_float_br("50.065"), 50065.0)

    def test_extracao_texto_com_media(self):
        texto = (
            "Situacao Inicial Jan/2024 Feb/20 24 Mar/2024 Media "
            "Instalacao Fiscal 1234567890 "
            "Requerida Trafo (kWh): 10.000 11.000 12.000 11.000 "
            "Injetada GDIS (kWh): 500 600 700 600 "
            "Energia Reversa (kWh): 200 250 300 250 "
            "Consumo Clientes (kWh): 8.000 9.000 10.000 9.000 "
            "IP Estimada (kWh): 300 300 300 300"
        )

        info = extrair_dados_pdf_text(texto)
        self.assertTrue(info["ok"])
        self.assertEqual(info["instalacao"], "1234567890")
        self.assertIn("Média", info["refs"])
        self.assertEqual(len(info["metricas"]["REQUERIDA"]), 4)

    def test_montagem_dataframe_por_referencia(self):
        texto = (
            "Situacao Inicial Jan/2024 Feb/2024 Mar/2024 Media "
            "Instalacao Fiscal 9876543210 "
            "Requerida Trafo (kWh): 1000 1100 1200 1100 "
            "Injetada GDIS (kWh): 100 110 120 110 "
            "Energia Reversa (kWh): 50 60 70 60 "
            "Consumo Clientes (kWh): 800 850 900 850 "
            "IP Estimada (kWh): 20 20 20 20"
        )

        info = extrair_dados_pdf_text(texto)
        df_media = montar_df_a_partir_pdf(info, "Média")
        self.assertEqual(df_media.iloc[0]["INSTALACAO"], "9876543210")
        self.assertEqual(float(df_media.iloc[0]["REQUERIDA"]), 1100.0)


if __name__ == "__main__":
    unittest.main()