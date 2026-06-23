from django import forms


def _parsear_lista_numeros(texto, nombre_campo, longitud_esperada=None):
    texto = texto.strip()
    if not texto:
        raise forms.ValidationError(f"Debes ingresar al menos un valor en '{nombre_campo}'.")
    partes = [p.strip() for p in texto.replace("\n", ",").split(",") if p.strip() != ""]
    valores = []
    for p in partes:
        try:
            valores.append(float(p))
        except ValueError:
            raise forms.ValidationError(f"'{p}' no es un número válido en '{nombre_campo}'.")
    if longitud_esperada and len(valores) != longitud_esperada:
        raise forms.ValidationError(
            f"'{nombre_campo}' debe tener exactamente {longitud_esperada} valores (uno por año), "
            f"pero ingresaste {len(valores)}."
        )
    return valores


class FlujoCajaForm(forms.Form):
    horizonte_anios = forms.IntegerField(
        label="Horizonte de evaluación (años)",
        min_value=1, max_value=30, initial=5,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Cantidad de años que se proyecta el flujo de caja del proyecto.",
    )
    inversion_inicial = forms.FloatField(
        label="Inversión inicial en activos ($)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 10000000"}),
        help_text="Desembolso en año 0 para comprar los activos necesarios para operar el proyecto.",
    )
    capital_trabajo = forms.FloatField(
        label="Capital de trabajo inicial ($)",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Recursos que la empresa debe mantener disponibles para financiar la operación (no se deprecia y se recupera íntegro al final del proyecto).",
    )
    valor_residual_activos = forms.FloatField(
        label="Valor de salvamento de los activos al final ($)",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Valor comercial estimado de los activos al término del horizonte de evaluación (antes de impuestos).",
    )
    ingresos_anuales = forms.CharField(
        label="Ingresos por venta de cada año",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Ej: 8000000, 8500000, 9000000, 9000000, 9000000"}),
        help_text="Un valor por cada año del horizonte. Si crecen, puedes ingresarlos directamente con su crecimiento ya aplicado.",
    )
    costos_anuales = forms.CharField(
        label="Costos y gastos de operación (sin depreciación) de cada año",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Ej: 4000000, 4200000, 4300000, 4300000, 4300000"}),
        help_text="Costos variables y fijos de operación (mano de obra, materiales, arriendo, etc.), sin incluir la depreciación: esta se calcula aparte.",
    )
    metodo_depreciacion = forms.ChoiceField(
        label="Método de depreciación",
        choices=(("lineal", "Normal (lineal)"), ("acelerada", "Acelerada (suma de dígitos)")),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="La depreciación acelerada no es un costo adicional: solo cambia el momento en que se reconoce, adelantando el ahorro de impuestos.",
    )
    valor_residual_contable = forms.FloatField(
        label="Valor residual contable de los activos (para depreciar) ($)",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Valor contable que queda sin depreciar al final de la vida útil (usualmente distinto al valor de salvamento comercial).",
    )
    tasa_impuesto = forms.FloatField(
        label="Tasa de impuesto a las utilidades (%)",
        initial=27,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Tasa de impuesto corporativo que se aplica sobre la utilidad antes de impuesto de cada año.",
    )
    tasa_descuento = forms.FloatField(
        label="Tasa de descuento del proyecto / WACC (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 12"}),
        help_text="Tasa usada para traer a valor presente el flujo de caja y calcular el VAN y la TIR del proyecto.",
    )

    def clean(self):
        cleaned = super().clean()
        n = cleaned.get("horizonte_anios")
        if not n:
            return cleaned
        if "ingresos_anuales" in cleaned:
            cleaned["ingresos_anuales"] = _parsear_lista_numeros(cleaned["ingresos_anuales"], "Ingresos anuales", n)
        if "costos_anuales" in cleaned:
            cleaned["costos_anuales"] = _parsear_lista_numeros(cleaned["costos_anuales"], "Costos anuales", n)
        return cleaned

    def clean_ingresos_anuales(self):
        return self.data.get("ingresos_anuales", "")  # se reprocesa en clean()

    def clean_costos_anuales(self):
        return self.data.get("costos_anuales", "")  # se reprocesa en clean()

    def clean_tasa_impuesto(self):
        return self.cleaned_data["tasa_impuesto"] / 100

    def clean_tasa_descuento(self):
        return self.cleaned_data["tasa_descuento"] / 100
