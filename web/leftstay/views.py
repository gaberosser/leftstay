from django.shortcuts import render, redirect, render_to_response


def home(request):
    return render(request, 'index.html')