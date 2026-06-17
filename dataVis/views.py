from django.shortcuts import render
import pandas as pd
import json


summary_course = pd.read_csv(r"C:\Users\bheywood\OneDrive - University of Dundee\Desktop\Dissertation\summary_course.csv")
summary_region = pd.read_csv(r"C:\Users\bheywood\OneDrive - University of Dundee\Desktop\Dissertation\summary_region.csv")


# results = [
#     {
#         'category': 'UG',
#         'region': 'Africa', 
#         'controlled': 'Yes', 
#         'fee_status': 'Overseas',
#         'date': '2026-06-07', 
#         'predicted_matrics': '35'
#     },
#         {
#         'category': 'UG',
#         'region': 'North America', 
#         'controlled': 'Yes', 
#         'fee_status': 'Overseas',
#         'date': '2026-06-07',
#         'predicted_matrics': '15'
#     }
# ]


def home(request):
    context = {
        'summary_course': summary_course.to_dict(orient="records"),
        'summary_region': summary_region.to_dict(orient="records"),
        'summary_course_json': json.dumps(summary_course.to_dict(orient="records")),
        'summary_region_json': json.dumps(summary_region.to_dict(orient="records")),
    }
    return render(request, 'dataVis/home.html', context)

def about(request):
    return render(request, 'dataVis/about.html')
