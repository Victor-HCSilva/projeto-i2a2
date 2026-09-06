class Cores:
    AZUL = '\033[94m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    LARANJA = '\033[33m'
    VERMELHO = '\033[91m'
    RESET = '\033[0m'


class Message:
    color = Cores()

    choice_colors = [
        'laranja',
        'amarelo',
        'verde',
        'azul',
        'vermelho'
    ]

    def danger(self, txt: str):
        print(f"{self.color.VERMELHO}{txt}{self.color.RESET}")

    def warning(self, txt: str):
        print(f"{self.color.AMARELO}{txt}{self.color.RESET}")

    def safe(self, txt: str):
        print(f"{self.color.VERDE}{txt}{self.color.RESET}")

    def very_safe(self, txt: str):
        print(f"{self.color.AZUL}{txt}{self.color.RESET}")

    def any_color(self, txt: str, option: str):
        match option:
            case 'laranja':
                print(f"{self.color.LARANJA}{txt}{self.color.LARANJA}")
            case 'vermelho':
                print(f"{self.color.VERMELHO}{txt}{self.color.RESET}")
            case 'verde':
                print(f"{self.color.VERDE}{txt}{self.color.RESET}")
            case 'amarelo':
                print(f"{self.color.AMARELO}{txt}{self.color.RESET}")
            case 'azul':
                print(f"{self.color.AZUL}{txt}{self.color.RESET}")
            case _:
                print(txt)


if __name__ == '__main__':
    color = Message()
    color.danger("Perigo!")
    color.warnig("Aviso")
    color.safe("Seguro")
    color.very_safe("Muito Seguro")
    color.any_color("Cor padrão" ,"violet")
    color.any_color("Azul", "azul") #Não existe
