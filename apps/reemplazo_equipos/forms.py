from django import forms


class VidaEconomicaForm(forms.Form):
    P = forms.FloatField(
        label="Precio del equipo nuevo (P)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 25000"}),
        help_text="Inversión inicial requerida para comprar el equipo (en la unidad monetaria que prefieras: $, US$, UF).",
    )
    A = forms.FloatField(
        label="Costo anual de mantención el primer año (A)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 11200"}),
        help_text="Costo de operación y mantención proyectado para el primer año de uso del equipo.",
    )
    g = forms.FloatField(
        label="Gradiente de deterioro anual (g)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 260"}),
        help_text="Cuánto aumentan los costos de mantención cada año adicional de uso, por el desgaste del equipo (g > 0).",
    )
    i = forms.FloatField(
        label="Costo de oportunidad del capital, WACC (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 6"}),
        help_text="Tasa de descuento anual usada para anualizar la inversión y los costos.",
    )
    n_inicial_tanteo = forms.IntegerField(
        label="Desde qué año tantear",
        initial=10, min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    n_final_tanteo = forms.IntegerField(
        label="Hasta qué año tantear",
        initial=20, min_value=2,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_i(self):
        return self.cleaned_data["i"] / 100

    def clean(self):
        cleaned = super().clean()
        ini, fin = cleaned.get("n_inicial_tanteo"), cleaned.get("n_final_tanteo")
        if ini and fin and ini >= fin:
            raise forms.ValidationError("El año inicial de tanteo debe ser menor que el año final.")
        if ini and fin and (fin - ini) > 40:
            raise forms.ValidationError("Usa un rango de tanteo de máximo 40 años para mantener la tabla legible.")
        return cleaned


class MomentoOptimoForm(forms.Form):
    nombre_actual = forms.CharField(
        label="Nombre de la alternativa actual",
        initial="Equipo defensor / Proceso manual",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cae_actual = forms.FloatField(
        label="CAE de la alternativa actual, hoy",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 600"}),
        help_text="Costo Anual Equivalente de seguir operando con lo que ya tienes (la máquina antigua o el proceso manual), proyectado para hoy.",
    )
    tasa_incremento = forms.FloatField(
        label="Tasa de incremento anual de ese costo (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 2.5"}),
        help_text="Cuánto crece, en porcentaje, el costo de la alternativa actual cada año (por deterioro, mayores remuneraciones, etc.).",
    )
    nombre_desafiante = forms.CharField(
        label="Nombre del equipo/proceso desafiante",
        initial="Equipo nuevo / Proceso automático",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cae_desafiante = forms.FloatField(
        label="CAE del equipo/proceso desafiante",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 681.7"}),
        help_text="Costo Anual Equivalente de reemplazar hoy por la opción nueva. Se asume constante en el tiempo.",
    )

    def clean_tasa_incremento(self):
        return self.cleaned_data["tasa_incremento"] / 100
