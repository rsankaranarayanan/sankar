# pylint: disable=protected-access
# pylint: disable=invalid-name

"""
This script can be used to collect information of Application (Start/Stop) status from,
Cf Services (Managed Services and User Provided Services) details in all cf organization and spaces.

This script has option for delete particular space and given application & application bind services.

"""
import argparse
import datetime
import xlsxwriter
from os import path
import sys
import getpass
from cloudfoundryapi import CfApi
import json
import yaml


# Cloud Foundry API host
API_HOST = '<< Cloud foundry API Host >>'

# Cloud Foundry Login Host
LOGIN_HOST = '<< Cloud Foundry Login Host >>'

DATE = str(datetime.date.today())
today = datetime.date.today()
YDate = str(today - datetime.timedelta(days=1))


def parse_args():
    """Parse command line args.

    Simple function to parse and return command line args.

    Returns:
        argparse.Namespace: An argparse.Namespace object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfUsername',
                        dest='cfUsername',
                        default=None,
                        required=True,
                        help='Provide Cloud Foundry User Name')
    parser.add_argument('-SDate',
                        dest='StartDate',
                        default=None,
                        required=False,
                        help='Enter start date to fetch events. Format YYYY-MM-DD')
    parser.add_argument('-EDate',
                        dest='EndDate',
                        default=None,
                        required=False,
                        help='Enter End date to fetch events. Format YYYY-MM-DD')
    args = parser.parse_args()
    return args


def cfapi_login(username, password):
    global cfapi
    cfapi = CfApi(username=username, password=password, login_host=LOGIN_HOST, api_host=API_HOST)
    return cfapi


def page_count(pagecount):
    pagenumber = 1
    while pagecount > 100:
        pagenumber += 1
        pagecount = pagecount - 100
    return pagenumber


def get_orginzation_list():
    orgcompletelistcount = cfapi.get_generic_request("/v2/organizations")['total_results']
    pagenumber = page_count(orgcompletelistcount)
    orgcompletelist = []
    for pg in range(pagenumber):
        temp_gen = (cfapi.get_generic_request1(
            "/v2/organizations?order-direction=asc&page=" + str(pg + 1) + "&results-per-page=100"))
        temp_assign = next(temp_gen)
        for tempass in temp_assign['resources']:
            orgcompletelist.append(tempass['entity']['name'])
    return orgcompletelist


def get_org_spaces_details(orgname):
    org_guid = cfapi.get_org_guid(orgname)
    oguid = cfapi.org_spaces(org_guid)
    spacelist = []
    for orgspace in oguid:
        sname = orgspace['entity']['name']
        spacelist.append({'name': sname, 'spaceurl': orgspace['metadata']['url']})
    return spacelist


def get_spacename(orgname):
    spaurl = get_org_spaces_details(orgname)
    spacename = []
    for spa in spaurl:
        spacename.append({'orgname': orgname, 'spacename': spa['name'], 'spaceguid': (spa['spaceurl']).split("/")[3]})
    return spacename


def get_app_url_details(appurl):
    app_details = []
    appdetails = cfapi.get_generic_request(appurl)
    for apd in appdetails['resources']:
        app_details.append({'name': apd['entity']['name'],
                            'state': apd['entity']['state'], 'date': apd['metadata']['updated_at']})
    return app_details


def get_app_status(orgname):
    spaurl = get_org_spaces_details(orgname)
    app_status = []
    for spa in spaurl:
        app_status.append({'orgname': orgname, 'SpaceName': spa['name'],
                           'app_state': get_app_url_details(spa['spaceurl'] + '/apps')})
    return app_status


def get_user_provider_service():
    userproviderservicecount = cfapi.get_generic_request("/v2/user_provided_service_instances")['total_results']
    pagenumber = page_count(userproviderservicecount)
    userproviderservice = []
    org_name = []
    for pg in range(pagenumber):
        temp_gen = (
            cfapi.get_generic_request1("/v2/user_provided_service_instances?order-direction=asc&page=" + str(pg + 1) +
                                       "&results-per-page=100"))
        temp_assign = next(temp_gen)
        for tempass in temp_assign['resources']:
            tempspace = cfapi.get_generic_request(tempass['entity']['space_url'])
            spacename = tempspace['entity']['name']
            orgid = tempspace['entity']['organization_guid']
            if orgid not in str(org_name):
                oname = cfapi.get_generic_request("/v2/organizations/" + orgid)['entity']['name']
                org_name.append({"orgname": oname, "orggid": orgid})
            for og in org_name:
                if orgid in str(og):
                    orgorganizations = og['orgname']
            userproviderservice.append(
                {'orgname': orgorganizations, 'name': tempass['entity']['name'],
                 'date': tempass['metadata']['created_at'], 'space_name': spacename})
    return userproviderservice


def get_service(orgname):
    spacedetails = get_org_spaces_details(orgname)
    service_status = []
    for space in spacedetails:
        userproviderservice = cfapi.get_generic_request(space['spaceurl'] + '/service_instances')
        for ser in userproviderservice['resources']:
            service_status.append({'orgname': orgname, 'name': ser['entity']['name'],
                                   'date': ser['entity']['last_operation']['created_at'],
                                   'space_name': space['name']})
    return service_status


def get_time_difference(tztimes):
    tztime = datetime.datetime.strptime(tztimes + '.001', '%Y-%m-%dT%H:%M:%S.%f')
    ltime = datetime.datetime.now()
    datetimeformat = '%Y-%m-%d %H:%M:%S.%f'
    diff = (datetime.datetime.strptime(str(ltime), datetimeformat) - datetime.datetime.strptime(str(tztime),
                                                                                                datetimeformat))
    return diff


def get_app_events(orgname, sdate, edate):
    appeventcount = cfapi.get_generic_request1("/v2/events?&order-direction=desc&q=timestamp>" + sdate +
                                               "T00:00:00Z&q=timestamp<" + edate + "T:23:59:00Z")
    appeventcount = next(appeventcount)['total_results']
    space_details = orgname
    pagenumber = page_count(appeventcount)
    appeventdetails = []
    org_name = []
    for pg in range(pagenumber):
        temp_gen = (cfapi.get_generic_request1("/v2/events?order-by=timestamp&order-by=id&page=" +
                                               str(pg + 1) + "&q=timestamp%3E" + sdate + "T00:00:00Z&q=timestamp%3C" +
                                               edate + "T:23:59:00Z&results-per-page=100"))
        temp_assign = next(temp_gen)
        for tempass in temp_assign['resources']:
            space_name = tempass['entity']['space_guid']
            if space_name not in str(space_details):
                sdetails = cfapi.get_generic_request("/v2/spaces/" + space_name)['entity']['name']
                space_details.append({'spacename': sdetails, 'spaceguid': space_name})
            for spn in space_details:
                for spname in spn:
                    if space_name in str(spname):
                        spacename = spname['spacename']
            orgid = tempass['entity']['organization_guid']
            if orgid not in str(org_name):
                oname = cfapi.get_generic_request("/v2/organizations/" + orgid)['entity']['name']
                org_name.append({"orgname": oname, "orggid": orgid})
            for og in org_name:
                if orgid in str(og):
                    orgorganizations = og['orgname']
            appeventdetails.append(
                {'OrgName': orgorganizations, 'SpaceName': spacename,
                 'Application_Name': tempass['entity']['actee_name'],
                 'User': tempass['entity']['actor_name'],
                 'Event': tempass['entity']['type'], "Time": str(tempass['entity']['timestamp'])})
    return appeventdetails


"""To get Particular organization and space details:"""

with open('input.yaml', "r") as INPUTF:
    INPUT = yaml.safe_load(INPUTF)


if INPUT['COMMON']:
    ssorg_name = INPUT['COMMON']['cf_org_name']
    ssspace_name = INPUT['COMMON']['cf_space_name']


if INPUT['CLOUDFOUNDRYSERVICENAMES']:
    vaultservice = INPUT['CLOUDFOUNDRYSERVICENAMES']['vaultservice']
    s3service = INPUT['CLOUDFOUNDRYSERVICENAMES']['s3service']
    rabbitmqservice = INPUT['CLOUDFOUNDRYSERVICENAMES']['rabbitmqservice']


def specific_space_cfapi_login(username, password):
    global sscfapi
    sscfapi = CfApi(username=username, password=password, login_host=LOGIN_HOST, api_host=API_HOST, org_name=ssorg_name,
                  space_name=ssspace_name)
    return sscfapi


def duplicate_elminate(inputstring):
    dupelimitapp = []
    for app in inputstring:
        if not re.match("^" + app + "$", str(dupelimitapp)):
            dupelimitapp.append(app)
    return dupelimitapp


def duplicate_elminate_services(inputstring):
    serdeplist = []
    for appname in inputstring:
        for value in globals()[appname]:
            if not re.match("^" + value['instance_name'] + "$", str(serdeplist)):
                serdeplist.append(value)
    return serdeplist


def get_app_env(appname):
    appguid = sscfapi.get_app_status(appname)
    appenv = sscfapi.get_generic_request('/v2/apps/' + appguid['guid'] + '/env')
    manage_services = []
    if appenv['system_env_json']['VCAP_SERVICES']:
        for env in appenv['system_env_json']['VCAP_SERVICES']:
            if "port" in str(appenv['system_env_json']['VCAP_SERVICES'][env]):
                for env1 in appenv['system_env_json']['VCAP_SERVICES'][env]:
                    manage_services.append(
                        {"instance_name": env1['instance_name'], "host": env1['credentials']['hostname'],
                         "username": env1['credentials']['username'], "password": env1['credentials']['password'],
                         "port": env1['credentials']['port'], 'db_name': env1['credentials']['db_name']})
            if s3service in str(appenv['system_env_json']['VCAP_SERVICES'][env]):
                for env1 in appenv['system_env_json']['VCAP_SERVICES'][env]:
                    manage_services.append(
                        {'instance_name': env1['instance_name'], 'bucket': env1['credentials']['bucket'],
                         'api_key': env1['credentials']['api_key'], 'secret_key': env1['credentials']['secret_key']})
            if "user-provided" in str(appenv['system_env_json']['VCAP_SERVICES'][env]):
                for env1 in appenv['system_env_json']['VCAP_SERVICES'][env]:
                    manage_services.append({'instance_name': env1['instance_name'], 'userprovided': 'yes'})
            if vaultservice in str(appenv['system_env_json']['VCAP_SERVICES'][env]):
                for env1 in appenv['system_env_json']['VCAP_SERVICES'][env]:
                    manage_services.append(
                        {'instance_name': env1['instance_name'], 'endpoint': env1['credentials']['endpoint'],
                         'service_secret_path': env1['credentials']['service_secret_path'],
                         'role_id': env1['credentials']['role_id'], 'secret_id': env1['credentials']['secret_id']})
    else:
        manage_services = "None"
    return manage_services


def generate_env():
    servicecredlist = []
    filedict = []
    if INPUT['APPLICATIONS']:
        dupelimitapp = duplicate_elminate(INPUT['APPLICATIONS'])
        for appnames in dupelimitapp:
            appenvname = (appnames).replace("-", "")
            appcheck = sscfapi.get_app_status(appnames)
            if len(appcheck) != 0:
                value = get_app_env(appnames)
                globals()[appenvname] = value
                servicecredlist.append(appenvname)
                filedict.append({appenvname: value})
    with open("tempcreds.txt", "w") as file:
        file.write(json.dumps(filedict))
    return servicecredlist


def get_service_credenital(servicename):
    servicecheck = sscfapi.verify_servicename(servicename)
    if servicecheck:
        vservicecred = sscfapi.get_service_credentials(servicename)
        return vservicecred


def delete_all_cfapps():
    if INPUT['APPLICATIONS']:
        dupelimitapp = duplicate_elminate(INPUT['APPLICATIONS'])
        delete_confirmation = raw_input(
            "Do you want to delete {0} applications, if yes, press y/Y else press n/N :".format(dupelimitapp))
        if delete_confirmation in ["y", "Y"]:
            for app in dupelimitapp:
                appcheck = sscfapi.get_app_status(app)
                if len(appcheck) != 0:
                    log("Deleting {0} application.".format(app))
                    sscfapi.user_delete_app(app)
                else:
                    log("{0} Application is not present.".format(app))
        else:
            log("{0} applications are not deleted.".format(dupelimitapp))


def service_delete_confirmation(servicecredlist):
    delete_service = []
    depservice = duplicate_elminate_services(servicecredlist)
    for sname in depservice:
        val = raw_input("If you want to delete {0}, Enter y/Y or Enter n/N :".format(sname['instance_name']))
        if val in ["y", "Y"]:
            delete_service.append(sname['instance_name'])
    return delete_service


def delete_services(servicecredlist):
    delete_service = service_delete_confirmation(servicecredlist)
    final_confirmation = raw_input(
        "Final confirmation for delete {0} services. If yes, Enter y/Y or Enter n/N :".format(delete_service))
    if final_confirmation in ["y", "Y"]:
        pass
    else:
        log("Services are not Deleted, as final confirmation is NO.\n \
            If you want to delete services, re-execute this script.")
        sys.exit("Script is exiting, because final confirmation of service deletion is NO. \n \
                 If you want to delete services, re-execute this script.\n")
    if servicecredlist:
        serdeplist1 = duplicate_elminate_services(servicecredlist)
        for value in serdeplist1:
            for dvalue in delete_service:
                servicename = value['instance_name']
                if servicename == dvalue:
                    if "userprovided" in str(value):
                        getstatus = sscfapi.get_user_provided_service(servicename)
                        if servicename in str(getstatus):
                            log('{0} Service Status check --> {1}'.format(servicename, getstatus))
                            sscfapi.user_provided_service_delete(servicename)
                            log('{0} Service is delete process initiated'.format(servicename))
                    else:
                        sstatus = sscfapi.get_service_status(servicename)
                        log('{0} Service Status check --> {1}'.format(servicename, sstatus))
                        if len(sstatus) != 0:
                            if sstatus['state'] != 'in progress' or sstatus['type'] != 'delete':
                                log('{0} Service is delete process initiated'.format(servicename))
                                sscfapi.user_delete_service(servicename)
                            else:
                                log('{0} Service can not be deleted, due {1}'.format(servicename, sstatus))
                        else:
                            log('{0} Service is not available.'.format(servicename))


def ssget_space(space_name):
    orguid = sscfapi.get_org_guid(ssorg_name)
    spaces = sscfapi.org_spaces(orguid)
    spaceguid = ''
    for space in spaces:
        if space['entity']['name'] == space_name:
            spaceguid = space['metadata']['guid']
    return spaceguid


def delete_space(space_name):
    spaceguid = ssget_space(space_name)
    log("{0} space delete operation initiated.".format(space_name))
    if spaceguid:
        sscfapi.delete_space("/v2/spaces/" + spaceguid)
    spaceguid1 = get_space()
    if not spaceguid1:
        spaceguid1 = 'NONE'
    if spaceguid1 != 'NONE':
        print(spaceguid1)
    else:
        log("After delete space, try to get space guid.\n")
        log("{0} space is not available. {0} space guid is {1}.".format(space_name, spaceguid1))


def main():
    args = parse_args()
    username = args.cfUsername
    print('Enter Ldap password to login Cloud Foundry')
    password = getpass.getpass('Password: ')
    cfapi_login(username, password)
    org_list = get_orginzation_list()
    spname = []
    appstatus = []
    serstatus = []
    for oglist in org_list:
        spname.append(get_spacename(oglist))
        appstatus.append(get_app_status(oglist))
        serstatus.append(get_service(oglist))
    if args.StartDate:
        SDate = args.StartDate
    else:
        SDate = YDate
    if args.EndDate:
        EDate = args.EndDate
    else:
        EDate = YDate
    appevent = get_app_events(spname, SDate, EDate)
    workbook = xlsxwriter.Workbook('cfdetails-' + DATE + '.xlsx')
    worksheet = workbook.add_worksheet("SPACE-Details")
    row = 1
    column = 0
    worksheet.write(0, 0, "ORG NAME")
    worksheet.write(0, 1, "SPACE NAME")
    for sp1 in spname:
        for sp in sp1:
            worksheet.write(row, column, sp['orgname'])
            worksheet.write(row, column + 1, sp['spacename'])
            row += 1
    worksheet = workbook.add_worksheet("Application")
    worksheet.write(0, 0, "ORG NAME")
    worksheet.write(0, 1, "SPACE NAME")
    worksheet.write(0, 2, "APPLICATION NAME")
    worksheet.write(0, 3, "STATUS")
    worksheet.write(0, 4, "DURATION of Since Start/Stop")
    row = 1
    column = 0
    for apstat in appstatus:
        for ass1 in apstat:
            for ass in ass1['app_state']:
                totalruntime = get_time_difference(str(ass['date']).strip("Z"))
                worksheet.write(row, column, ass1['orgname'])
                worksheet.write(row, column + 1, ass1['SpaceName'])
                worksheet.write(row, column + 2, ass['name'])
                worksheet.write(row, column + 3, ass['state'])
                worksheet.write(row, column + 4, str(totalruntime))
                row += 1
    userprovidestatus = get_user_provider_service()
    worksheet = workbook.add_worksheet("Services")
    worksheet.write(0, 0, "ORG NAME")
    worksheet.write(0, 1, "SPACE NAME")
    worksheet.write(0, 2, "SERVICE NAME")
    worksheet.write(0, 3, "RUNNING DURATION")
    row = 1
    column = 0
    for serstat in serstatus:
        for sstate in serstat:
            totalruntime = get_time_difference(str(sstate['date']).strip("Z"))
            worksheet.write(row, column, sstate['orgname'])
            worksheet.write(row, column + 1, sstate['space_name'])
            worksheet.write(row, column + 2, sstate['name'])
            worksheet.write(row, column + 3, str(totalruntime))
            row += 1
    for sstate in userprovidestatus:
        totalruntime = get_time_difference(str(sstate['date']).strip("Z"))
        worksheet.write(row, column, sstate['orgname'])
        worksheet.write(row, column + 1, sstate['space_name'])
        worksheet.write(row, column + 2, sstate['name'])
        worksheet.write(row, column + 3, str(totalruntime))
        row += 1
    worksheet = workbook.add_worksheet("App Events")
    worksheet.write(0, 0, "ORG NAME")
    worksheet.write(0, 1, "SPACE NAME")
    worksheet.write(0, 2, "Application Name")
    worksheet.write(0, 3, "User")
    worksheet.write(0, 4, "Event")
    worksheet.write(0, 5, "Time")
    row = 1
    column = 0
    for apevent in appevent:
        worksheet.write(row, column, apevent['OrgName'])
        worksheet.write(row, column + 1, apevent['SpaceName'])
        worksheet.write(row, column + 2, apevent['Application_Name'])
        worksheet.write(row, column + 3, apevent['User'])
        worksheet.write(row, column + 4, apevent['Event'])
        worksheet.write(row, column + 5, apevent['Time'])
        row += 1
    workbook.close()

""" Below will be used for specific organization and space access"""
    specific_space_cfapi_login(org_name, space_name, username, password)
    if args.func == "delete_space":
        delete_space()
    else:
        if path.isfile("tempcreds.txt"):
            servicecredlist = []
            with open("tempcreds.txt", "r") as f:
                servicecredlist1 = yaml.safe_load(f)
            for ser in servicecredlist1:
                for ser1 in ser:
                    servicecredlist.append(ser1)
                    globals()[ser1] = ser[ser1]
        else:
            servicecredlist = generate_env()
    delete_all_cfapps()
    delete_services()




if __name__ == '__main__':
    main()
