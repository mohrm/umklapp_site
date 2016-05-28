from django import template
register = template.Library()

@register.filter(name='countup') 
def countup(number):
    return range(number)

