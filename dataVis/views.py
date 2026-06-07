from django.shortcuts import render

results = [
    {
        'category': 'UG',
        'region': 'Africa', 
        'controlled': 'Yes', 
        'fee_status': 'Overseas',
        'date': '2026-06-07', 
        'predicted_matrics': '35'
    },
        {
        'category': 'UG',
        'region': 'North America', 
        'controlled': 'Yes', 
        'fee_status': 'Overseas',
        'date': '2026-06-07',
        'predicted_matrics': '15'
    }
]

def home(request):
    context = { 
        'results': results
    }
    return render(request, 'dataVis/home.html', context)

def about(request):
    return render(request, 'dataVis/about.html')
