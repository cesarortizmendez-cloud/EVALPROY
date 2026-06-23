"""
Formularios del módulo VAN / TIR / Payback / Fisher / IVAN.

Los flujos de caja se ingresan como texto separado por comas para evitar
depender de JavaScript para filas dinámicas (funciona igual de bien en
escritorio y celular, y es más robusto). Se valida y convierte a lista
de floats en clean_flujos().
"""
from django import forms


def _parsear_lista_numeros(texto: str, nombre_campo: str) -> list[float]:
    texto = texto.strip()
    if not texto:
        raise forms.ValidationError(f"Debes ingresar al menos un valor en '{nombre_campo}'.")
    partes = [p.strip() for p in texto.replace("\n", ",").split(",") if p.strip() != ""]
    valores = []
    for p in partes:
        try:
            valores.append(float(p))
        except ValueError:
            raise forms.ValidationError(
                f"'{p}' no es un número válido en '{nombre_campo}'. Usa solo números y comas."
            )
    return valores


class VanTirForm(forms.Form):
    flujos = forms.CharField(
        label="Flujos de caja (año 0, año 1, año 2, …)",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Ej: -1000000, 400000, 450000, 500000",
            "class": "form-control",
        }),
        help_text=(
            "Ingresa los flujos separados por comas. El PRIMER valor (año 0) es la inversión "
            "inicial y normalmente se escribe negativo, ej. -1000000. Los siguientes son los "
            "flujos netos de cada año del proyecto (positivos si son utilidad, negativos si "
            "hay pérdida o nueva inversión ese año)."
        ),
    )
    tasa_descuento = forms.FloatField(
        label="Tasa de descuento anual (%)",
        min_value=-99,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 10"}),
        help_text=(
            "Es el costo de oportunidad del capital: la rentabilidad mínima que exiges al "
            "proyecto, normalmente el WACC. Ingresa el número en porcentaje, ej. 10 para 10%."
        ),
    )
    tasa_corte_tir = forms.FloatField(
        label="Tasa de corte para comparar con la TIR (%) — opcional",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Igual a la tasa de descuento si la dejas vacía"}),
        help_text="Si la dejas vacía, se usa la misma tasa de descuento ingresada arriba.",
    )
    periodo_maximo_payback = forms.FloatField(
        label="Período máximo aceptable de Payback (años) — opcional",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "placeholder": "Ej: 3"}),
        help_text="Si tu política exige recuperar la inversión antes de cierto plazo, ingrésalo aquí para evaluar el cumplimiento.",
    )

    def clean_flujos(self):
        return _parsear_lista_numeros(self.cleaned_data["flujos"], "Flujos de caja")

    def clean_tasa_descuento(self):
        return self.cleaned_data["tasa_descuento"] / 100

    def clean_tasa_corte_tir(self):
        valor = self.cleaned_data.get("tasa_corte_tir")
        return valor / 100 if valor is not None else None


class ComparacionFisherForm(forms.Form):
    nombre_a = forms.CharField(label="Nombre Proyecto A", initial="Proyecto A",
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    flujos_a = forms.CharField(
        label="Flujos Proyecto A",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "-1000000, 0, 0, 1700000"}),
    )
    nombre_b = forms.CharField(label="Nombre Proyecto B", initial="Proyecto B",
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    flujos_b = forms.CharField(
        label="Flujos Proyecto B",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "-1000000, 500000, 500000, 500000"}),
    )

    def clean_flujos_a(self):
        return _parsear_lista_numeros(self.cleaned_data["flujos_a"], "Flujos Proyecto A")

    def clean_flujos_b(self):
        return _parsear_lista_numeros(self.cleaned_data["flujos_b"], "Flujos Proyecto B")


class FilaNoPeriodicaForm(forms.Form):
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
        help_text="",
    )
    flujo = forms.FloatField(
        label="Flujo ($)",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm", "placeholder": "Ej: -10000 o 5000"}),
    )


from django.forms import formset_factory

FilaNoPeriodicaFormSet = formset_factory(FilaNoPeriodicaForm, extra=4, min_num=2, validate_min=True)


class TasaNoPeriodicaForm(forms.Form):
    tasa_descuento = forms.FloatField(
        label="Tasa de descuento anual (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 11"}),
        help_text="Igual que en VAN.NO.PER de Excel: la tasa anual a la que se descuentan los flujos según los días reales transcurridos (base 365 días).",
    )
    tasa_corte_tir = forms.FloatField(
        label="Tasa de corte para comparar con la TIR (%) — opcional",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Si la dejas vacía, se usa la misma tasa de descuento.",
    )

    def clean_tasa_descuento(self):
        return self.cleaned_data["tasa_descuento"] / 100

    def clean_tasa_corte_tir(self):
        v = self.cleaned_data.get("tasa_corte_tir")
        return v / 100 if v is not None else None
