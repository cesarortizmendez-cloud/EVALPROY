from django import forms


class CAPMForm(forms.Form):
    tasa_libre_riesgo = forms.FloatField(
        label="Tasa libre de riesgo (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 4"}),
        help_text="Rentabilidad de un activo sin riesgo de no pago, típicamente bonos del banco central o del tesoro a largo plazo.",
    )
    beta = forms.FloatField(
        label="Beta del proyecto/empresa",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 1.2"}),
        help_text="Mide el riesgo sistemático: cuánto se mueve el retorno del proyecto en relación al mercado. Beta=1 se mueve igual que el mercado; Beta>1 amplifica sus movimientos.",
    )
    premio_riesgo_mercado = forms.FloatField(
        label="Premio por riesgo de mercado, (Rm − Rf) (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 6"}),
        help_text="Diferencia entre la rentabilidad esperada del mercado (Rm) y la tasa libre de riesgo (Rf). Es lo extra que exige el mercado por invertir en activos riesgosos.",
    )

    def clean_tasa_libre_riesgo(self):
        return self.cleaned_data["tasa_libre_riesgo"] / 100

    def clean_premio_riesgo_mercado(self):
        return self.cleaned_data["premio_riesgo_mercado"] / 100


class BetaForm(forms.Form):
    ACCION = (("desapalancar", "Desapalancar (quitar efecto de deuda)"),
               ("apalancar", "Apalancar (agregar efecto de deuda)"))
    accion = forms.ChoiceField(choices=ACCION, widget=forms.Select(attrs={"class": "form-select"}))
    beta_dado = forms.FloatField(
        label="Beta conocido",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Si vas a desapalancar, ingresa el Beta apalancado (observado en el mercado). Si vas a apalancar, ingresa el Beta desapalancado (del activo, sin deuda).",
    )
    deuda = forms.FloatField(label="Deuda (D)", widget=forms.NumberInput(attrs={"class": "form-control"}))
    patrimonio = forms.FloatField(label="Patrimonio (E)", widget=forms.NumberInput(attrs={"class": "form-control"}))
    tasa_impuesto = forms.FloatField(
        label="Tasa de impuesto corporativo (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 27"}),
    )

    def clean_tasa_impuesto(self):
        return self.cleaned_data["tasa_impuesto"] / 100


class WACCForm(forms.Form):
    ke = forms.FloatField(
        label="Costo del patrimonio, Ke (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Rentabilidad exigida por los accionistas. Puedes calcularlo en la pestaña CAPM y traerlo aquí.",
    )
    kd = forms.FloatField(
        label="Costo de la deuda, Kd (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Tasa de interés que paga la empresa por su deuda (antes de impuestos).",
    )
    valor_patrimonio = forms.FloatField(
        label="Valor del patrimonio (E)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    valor_deuda = forms.FloatField(
        label="Valor de la deuda (D)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    tasa_impuesto = forms.FloatField(
        label="Tasa de impuesto corporativo (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 27"}),
        help_text="Reduce el costo efectivo de la deuda gracias al escudo tributario de los intereses.",
    )

    def clean_ke(self):
        return self.cleaned_data["ke"] / 100

    def clean_kd(self):
        return self.cleaned_data["kd"] / 100

    def clean_tasa_impuesto(self):
        return self.cleaned_data["tasa_impuesto"] / 100
