import os
import mimetypes
import sys
import django
import requests
import logging
import json
import traceback
import pyodbc
import datetime
import xlrd
from arcgis.gis import GIS
import pprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rtaa_gis.settings'
django.setup()

from lpm.serializers import AgreementSerializer
from lpm.models import Agreement as AgreementModel

from django.conf import settings

##############################################
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/ABM_bridge.txt")
file = open(log_path, 'w')
file.close()


def loggit(text):
    file = open(log_path, 'a')
    file.write("{}\n".format(text))
    pprint.pprint("{}\n".format(text))
    file.close()


###############################################
kwargs = dict()
kwargs['driver'] = '{SQL Server}'
kwargs['server'] = 'Reno-fis-sql2'
kwargs['database'] = 'ABM_Reno_GIS'

connGIS = pyodbc.connect(**kwargs)

kwargs['database'] = 'ABM_Reno_Prod'
connPROD = pyodbc.connect(**kwargs)

# TODO - do not include the Baggage Service Fees of type Security Service
# TODO - do not include the Stead Ground Leases


def queryConnection(connection):
    """take in the _mssql connection and write out geometries"""
    # query each connection database
    data = {}
    status_types = {
        "ACTV": "Active",
        "MTM": "Month-to-Month",
        "YTY": "Year-to-Year",
        "PEND": "Pending"
    }
    agreement_types = {}
    cursor = connection.cursor()
    # # get the Agreement Type Descriptions into an object
    cursor.execute("SELECT [pkAgreementTypeID], [AgreementTypeDescription]\
    FROM [ABM_Reno_Prod].[dbo].[trefagTypes]")
    for row in cursor:
        agreement_types[row[0]] = row[1]

    # get the NON-STEAD Agreements
    cursor.execute("SELECT [pkAgreementID],\
    [AgreementNumber],[AgreementTitle],\
    [fkAgreementStatusID], [AgreementDescription],\
    [fkAgreementTypeID]\
     FROM [ABM_Reno_Prod].[dbo].[tblagAgreements]\
        WHERE [fkAgreementTypeID] <> 'STEADGRND'")
    for row in cursor:
        # keep the object if an active/or pending type
        if row[3].upper() in status_types.keys():
            # Ignore the Badging Service Fee Agreements
            if "BADGING" not in row[2].upper():
                data[row[0]] = {
                    "AgreementNumber": row[1],
                    "AgreementTitle": row[2],
                    "AgreementStatus": status_types[row[3]],
                    "AgreementDescription": row[4],
                    "AgreementType": agreement_types[row[5]]
                }

    ids = data.keys()
    for key in ids:
        cursor.execute("SELECT [fkAgreementID], \
        [fkDateTypeID], [DateValue]\
        FROM [ABM_Reno_Prod].[dbo].[tblagAgreementDates]\
        WHERE [fkAgreementID] = '{}'".format(key))
        for row in cursor:
            try:
                id_int = int(row[0])
                if id_int == key:
                    date_type = row[1]
                    date_value = row[2]
                    if date_type in ["EXEC", "START"]:
                        data[key]["StartDate"] = date_value.date()
                        # data[key]["StartDate"] = date_value
                    if date_type in ["END", "EXPIR"]:
                        data[key]["Expiration"] = date_value.date()
                        # data[key]["Expiration"] = date_value
                    # if the start date or the end date have not been set, make it Unknown
                    existing_fields = data[key].keys()
                    if "StartDate" not in existing_fields:
                        data[key]["StartDate"] = None
                    if "Expiration" not in existing_fields:
                        data[key]["Expiration"] = None
            except Exception as e:
                loggit(e)

    try:
        # before returning this object, verify every value has each of the time-enabling properties needed
        ids_no_date = []
        for k, v in data.items():
            keys = v.keys()
            fields = ["StartDate", "Expiration"]
            for f in fields:
                if f not in keys:
                    ids_no_date.append(k)
                    data[k][f] = None

        ids_no_date = list(set(ids_no_date))
        if ids_no_date:
            cursor.execute("SELECT [fkAgreementID] \
                   FROM [ABM_Reno_Prod].[dbo].[tblagAgreementDates]")
            for row in cursor:
                if row[0] in ids_no_date:
                    ids_no_date.remove(row[0])
            if ids_no_date:
                loggit("These Agreement IDs were not found in the Date Table :: {}\n".format(ids_no_date))
    except Exception as e:
        loggit("Error when checking object fields")
    return data


if __name__ == "__main__":
    try:
        x = queryConnection(connPROD)

        for id in x:
            data = {
                "id": id,
                "title": x[id]["AgreementTitle"],
                "type": x[id]["AgreementType"],
                "description": x[id]["AgreementDescription"],
                "status": x[id]["AgreementStatus"],
                "start_date": x[id]["StartDate"],
                "end_date": x[id]["Expiration"]
            }

            try:
                existing = AgreementModel.objects.get(id=id)
                serial = AgreementSerializer(existing, data=data)
            except AgreementModel.DoesNotExist:
                serial = AgreementSerializer(data=data)

            if serial.is_valid():
                serial.save()
            else:
                loggit("Unable to save agreement to db :: {} : {}".format(serial.errors, data))

        # Query the tables and update the data in AGOL

        gis = GIS("https://www.arcgis.com", "data_owner", "GIS@RTAA123!")
        layer = gis.content.get('fcd67e3684d44bf7a0052cdc2e52043b')

        feature_layer = layer.layers[0]

        for agg in AgreementModel.objects.all():
            feature_set = feature_layer.query(where="Agreement={}".format(int(agg.id)))
            if len(feature_set.features):
                filtered = feature_set.features
                for lyr in filtered:
                    lyr.attributes["AGREEMENT_TYPE"] = agg.type
                    lyr.attributes["START_DATE"] = str(agg.start_date)
                    lyr.attributes["END_DATE"] = str(agg.end_date)
                    lyr.attributes["TENANT_NAME"] = agg.title
                    lyr.attributes["LEASE_STATUS"] = agg.status

                    try:
                        update_result = feature_layer.edit_features(updates=[lyr])
                    except RuntimeError as e:
                        loggit(e)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        loggit(e)

