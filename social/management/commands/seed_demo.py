from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from social.models import Profile,Tweet,Follow

class Command(BaseCommand):
    help="Cria perfis e publicações fictícios para demonstração visual (sem senhas utilizáveis)."
    def handle(self,*args,**kwargs):
        examples=[
            ("ana.dev","Ana Oliveira","Construindo coisas para a web. Python, café e boas ideias.","Uma API bem pensada começa pelas pessoas que vão usá-la. Hoje reorganizei os endpoints do meu projeto e tudo ficou mais claro. ✳"),
            ("lucas.py","Lucas Santos","Aprendendo em público, um projeto de cada vez.","Pequena vitória do dia: primeiro teste de integração passando no Django! Ver o fluxo completo funcionando dá outra confiança."),
            ("marina.design","Marina Costa","Interfaces simples para problemas reais.","Bom design também é saber o que deixar de fora. Menos campos, mais clareza e uma boa conversa com quem usa o produto."),
        ]
        for username,name,bio,body in examples:
            user,created=get_user_model().objects.get_or_create(username=username)
            if created:user.set_unusable_password();user.save()
            Profile.objects.get_or_create(user=user,defaults={"display_name":name,"bio":bio})
            Tweet.objects.get_or_create(author=user,body=body)
        self.stdout.write(self.style.SUCCESS("Perfis fictícios criados sem senhas de acesso."))
