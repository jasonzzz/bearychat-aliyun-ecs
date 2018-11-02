import time, os
from concurrent.futures import ThreadPoolExecutor
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode
from .base import BaseHandler

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstanceStatusRequest, DescribeInstanceAttributeRequest, DescribeVpcsRequest, DescribeRegionsRequest, DescribeZonesRequest, DescribeImagesRequest, CreateInstanceRequest, DeleteInstanceRequest, DescribeInstanceMonitorDataRequest, StartInstanceRequest, StopInstanceRequest, RunInstancesRequest, AllocateEipAddressRequest, AssociateEipAddressRequest

# TODO: https://help.aliyun.com/document_detail/74686.html
class AliyunHandler(BaseHandler):
    def initialize(self):
        self.aliyun_token = {'id': '', 'secret': ''}
        self.usages = {
                'list': 'list $region\nref: https://help.aliyun.com/document_detail/40654.html',
                'show': 'show $region $instanceId',
#                'avail': 'avail [region|zone $region]',
                'avail-regions': 'avail-regions',
                'avail-zones': 'avail-zones $region, TODO: avail-zones AvailableInstanceType/AvailableResources',
                'avail-images': 'avail-images $region',
                'create': 'create $region $templateName $instanceName, FIXME: only support launch template',
                'monitor-5min': 'monitor-5min $region $instanceId',
                'start': 'start $region $instanceId',
                'stop': 'stop $region $instanceId',
                'delete': 'delete $region $instanceId',
                }
        self.usages['__ELSE__'] = 'help [subcommand]\n  subcommand: %s' % ', '.join(self.usages.keys())

        self.executor = ThreadPoolExecutor(os.cpu_count())

    def status_color(self, status):
        color = 'white'
        if status == 'Pending':
            color = 'yellow'
        elif status == 'Starting':
            color = 'cyan'
        elif status == 'Running':
            color = 'green'
        elif status == 'Stopping':
            color = 'pink'
        elif status == 'Stopped':
            color = 'red'

        return color

    @gen.coroutine
    def post(self):
        d = json_decode(self.request.body)
        if not super().is_authorized(d['token']):
            self.write('{"text": "invalid bearychat token"}')
            return

        d['text'] = d['text'].strip()
        trigger = d['text'].split(' ')[0].strip()
        try:
            command = str(d['text'].split(' ')[1].strip())
        except IndexError:
            self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages['__ELSE__']))
            return

        if command == 'help':
            try:
                subcommand = d['text'].split(' ')[2].strip()
            except IndexError:
                subcommand = '__ELSE__'

            try:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[subcommand]))
            except KeyError:
                self.write('{"text": "Usage: %s help [subcommand]"}' % (trigger))
            return

        params = {}
        # RESP status https://help.aliyun.com/document_detail/25687.html
        if command == 'list':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_list(params['region'])
            self.write(result)

        # TODO: securityGroup
        if command == 'show':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['instanceId'] = d['text'].split(' ')[3].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_show(params['region'], params['instanceId'])
            self.write(result)

        if command == 'avail-regions':
            result = yield self.do_avail_regions()
            self.write(result)

        if command == 'avail-zones':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_avail_zones(params['region'])
            self.write(result)

        if command == 'avail-images':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_avail_images(params['region'])
            self.write(result)

        if command == 'start':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['instanceId'] = d['text'].split(' ')[3].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_start(params['region'], params['instanceId'])
            self.write(result)

        if command == 'stop':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['instanceId'] = d['text'].split(' ')[3].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_stop(params['region'], params['instanceId'])
            self.write(result)

        # FIXME: only support launch template
        if command == 'create':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['template_name'] = d['text'].split(' ')[3].strip()
                params['instance_name'] = d['text'].split(' ')[4].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            yield self.do_create(params['region'], params['template_name'], params['instance_name'])

        if command == 'delete':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['instanceId'] = d['text'].split(' ')[3].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_delete(params['region'], params['instanceId'])
            self.write(result)

        if command == 'monitor-5min':
            try:
                params['region'] = d['text'].split(' ')[2].strip()
                params['imageId'] = d['text'].split(' ')[3].strip()
            except IndexError:
                self.write('{"text": "Usage: %s %s"}' % (trigger, self.usages[command]))
                return

            result = yield self.do_monitor_5min(params['region'], params['imageId'])
            self.write(result)

    @run_on_executor
    def do_list(self, region_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)
        describeInstanceStatusRequest = DescribeInstanceStatusRequest.DescribeInstanceStatusRequest()
        # TODO: set_PageSize, set_PageNumber
        describeInstanceStatusRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceStatusRequest))
        result = {}
        result['text'] = 'list %s\ntotal: %s' % (region_id, resp['TotalCount'])
        result['attachments'] = []
        for i in resp['InstanceStatuses']['InstanceStatus']:
            describeInstanceAttributeRequest = DescribeInstanceAttributeRequest.DescribeInstanceAttributeRequest()
            describeInstanceAttributeRequest.set_InstanceId(i['InstanceId'])
            describeInstanceAttributeRequest.set_accept_format('json')

            resp1 = json_decode(client.do_action(describeInstanceAttributeRequest))

            result['attachments'].append({"title": "%s (%s)" % (resp1['InstanceName'], resp1['InstanceId']), "text": "%s" % resp1['Status'], "color": "%s" % self.status_color(resp1['Status'])})

        return result

    @run_on_executor
    def do_show(self, region_id, instance_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)
        describeInstanceAttributeRequest = DescribeInstanceAttributeRequest.DescribeInstanceAttributeRequest()
        describeInstanceAttributeRequest.set_InstanceId(instance_id)
        describeInstanceAttributeRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceAttributeRequest))
        result = {}
        result['text'] = 'show %s %s' % (region_id, instance_id)
        if 'Code' in resp.keys() and resp['Code'] == 'InvalidInstanceId.NotFound':
            result['text'] = 'show %s %s failed, %s' % (region_id, instance_id, resp['Code'])
        else:
            if resp['InstanceNetworkType'] == 'classic':
                result['attachments'] = [{"title": "%s (%s)" % (resp['InstanceName'], resp['InstanceId']), "text": "InstanceType: %s\nMemory: %s MB\nCpu: %s\nZoneId: %s\nRegionId: %s\nStatus: %s\nIoOptimized: %s\nInstanceNetworkType: %s\nPublicIpAddress: %s\nCreationTime: %s\nExpiredTime: %s" % (resp['InstanceType'], resp['Memory'], resp['Cpu'], resp['ZoneId'], resp['RegionId'], resp['Status'], resp['IoOptimized'], resp['InstanceNetworkType'], ', '.join(resp['PublicIpAddress']['IpAddress']), resp['CreationTime'], resp['ExpiredTime']), "color": "%s" % self.status_color(resp['Status'])}]
            elif resp['InstanceNetworkType'] == 'vpc':
                result['attachments'] = [{"title": "%s (%s)" % (resp['InstanceName'], resp['InstanceId']), "text": "InstanceType: %s\nMemory: %s MB\nCpu: %s\nZoneId: %s\nRegionId: %s\nStatus: %s\nIoOptimized: %s\nInstanceNetworkType: %s\nEipAddress: %s\nCreationTime: %s\nExpiredTime: %s" % (resp['InstanceType'], resp['Memory'], resp['Cpu'], resp['ZoneId'], resp['RegionId'], resp['Status'], resp['IoOptimized'], resp['InstanceNetworkType'], resp['EipAddress']['IpAddress'], resp['CreationTime'], resp['ExpiredTime']), "color": "%s" % self.status_color(resp['Status'])}]

        return result

    @run_on_executor
    def do_avail_regions(self):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'])
        describeRegionRequest = DescribeRegionsRequest.DescribeRegionsRequest()
        describeRegionRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeRegionRequest))
        result = {}
        result['text'] = 'avail regions'
        result['attachments'] = []
        for i in resp['Regions']['Region']:
            result['attachments'].append({"title": "%s" % i['LocalName'], "text": "%s" % i['RegionId']})

        return result

    @run_on_executor
    def do_avail_zones(self, region_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)
        describeZonesRequest = DescribeZonesRequest.DescribeZonesRequest()
        describeZonesRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeZonesRequest))
        result = {}
        result['text'] = 'avail zones'
        result['attachments'] = []
        for i in resp['Zones']['Zone']:
            result['attachments'].append({"title": "%s" % i['LocalName'], "text": "InstanceType: %s" % ', '.join(i['AvailableInstanceTypes']['InstanceTypes'])})

        return result

    @run_on_executor
    def do_avail_images(self, region_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        describeImagesRequest = DescribeImagesRequest.DescribeImagesRequest()
        describeImagesRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeImagesRequest))
        result = {}
        result['text'] = 'avail images %s' % region_id
        result['attachments'] = []
        for i in resp['Images']['Image']:
            result['attachments'].append({"title": "%s (%s)" % (i['ImageName'], i['ImageId']), "text": "OSName: %s" % i['OSName']})

        return result

    @run_on_executor
    def do_start(self, region_id, instance_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        # check status first
        describeInstanceAttributeRequest = DescribeInstanceAttributeRequest.DescribeInstanceAttributeRequest()
        describeInstanceAttributeRequest.set_InstanceId(instance_id)
        describeInstanceAttributeRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceAttributeRequest))

        result = {}
        # check if exist
        if 'Code' in resp.keys() and resp['Code'] == 'InvalidInstanceId.NotFound':
            result['text'] = 'start %s %s failed, %s' % (region_id, instance_id, resp['Code'])
        else:
            if resp['Status'] != 'Stopped':
                result['text'] = 'start %s %s failed' % (region_id, instance_id)
                result['attachments'] = [{"title": "%s" % resp['InstanceId'], "text": "%s" % resp['Status'], "color": "%s" % self.status_color(resp['Status'])}]
            else:
                startInstanceRequest = StartInstanceRequest.StartInstanceRequest()
                startInstanceRequest.set_InstanceId(instance_id)
                startInstanceRequest.set_accept_format('json')

                resp = json_decode(client.do_action(startInstanceRequest))
                result['text'] = 'starting instance %s %s' % (region_id, instance_id)

        return result

    @run_on_executor
    def do_stop(self, region_id, instance_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        # check status first
        describeInstanceAttributeRequest = DescribeInstanceAttributeRequest.DescribeInstanceAttributeRequest()
        describeInstanceAttributeRequest.set_InstanceId(instance_id)
        describeInstanceAttributeRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceAttributeRequest))

        result = {}
        # check if exist
        if 'Code' in resp.keys() and resp['Code'] == 'InvalidInstanceId.NotFound':
            result['text'] = 'stop %s %s failed, %s' % (region_id, instance_id, resp['Code'])
        else:
            if resp['Status'] != 'Running':
                result['text'] = 'stop %s %s failed' % (region_id, instance_id)
                result['attachments'] = [{"title": "%s" % resp['InstanceId'], "text": "%s" % resp['Status'], "color": "%s" % self.status_color(resp['Status'])}]
            else:
                stopInstanceRequest = StopInstanceRequest.StopInstanceRequest()
                stopInstanceRequest.set_InstanceId(instance_id)
                stopInstanceRequest.set_accept_format('json')

                client.do_action(stopInstanceRequest)
                result['text'] = 'stopping instance %s %s' % (region_id, instance_id)

        return result

    @run_on_executor
    def do_create(self, region_id, template_name, instance_name):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        # Step 1, run instance from launch template
        runInstancesRequest = RunInstancesRequest.RunInstancesRequest()
        runInstancesRequest.set_LaunchTemplateName(template_name)
        runInstancesRequest.set_accept_format('json')
        runInstancesRequest.set_InstanceName(instance_name)

        resp = json_decode(client.do_action(runInstancesRequest))
        instanceId = resp['InstanceIdSets']['InstanceIdSet'][0]

        # Step 2, allocate eip
        allocateEipAddressRequest = AllocateEipAddressRequest.AllocateEipAddressRequest()
        allocateEipAddressRequest.set_InternetChargeType('PayByTraffic')
        #allocateEipAddressRequest.set_InstanceChargeType('PostPaid')
        allocateEipAddressRequest.set_accept_format('json')

        resp = json_decode(client.do_action(allocateEipAddressRequest))
        ipAddress = resp['EipAddress']
        allocationId = resp['AllocationId']

        time.sleep(30)

        # Step 3, associate eip
        associateEipAddressRequest = AssociateEipAddressRequest.AssociateEipAddressRequest()
        associateEipAddressRequest.set_AllocationId(allocationId)
        associateEipAddressRequest.set_InstanceId(instanceId)
        associateEipAddressRequest.set_accept_format('json')

        client.do_action(associateEipAddressRequest)

    @run_on_executor
    def do_delete(self, region_id, instance_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        # check status first
        describeInstanceAttributeRequest = DescribeInstanceAttributeRequest.DescribeInstanceAttributeRequest()
        describeInstanceAttributeRequest.set_InstanceId(instance_id)
        describeInstanceAttributeRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceAttributeRequest))

        result = {}
        # check if exist
        if 'Code' in resp.keys() and resp['Code'] == 'InvalidInstanceId.NotFound':
            result['text'] = 'delete %s %s failed, %s' % (region_id, instance_id, resp['Code'])
        else:
            if resp['Status'] != 'Stopped':
                result['text'] = 'delete %s %s failed, stop instance first' % (region_id, instance_id)
                result['attachments'] = [{"title": "%s" % resp['InstanceId'], "text": "%s" % resp['Status'], "color": "%s" % self.status_color(resp['Status'])}]
            else:
                deleteInstanceRequest = DeleteInstanceRequest.DeleteInstanceRequest()
                deleteInstanceRequest.set_InstanceId(instance_id)
                deleteInstanceRequest.set_accept_format('json')

                client.do_action(deleteInstanceRequest)
                result['text'] = 'deleting instance %s %s' % (region_id, instance_id)

        return result

    @run_on_executor
    def do_monitor_5min(self, region_id, image_id):
        client = AcsClient(self.aliyun_token['id'], self.aliyun_token['secret'], region_id)

        describeInstanceMonitorDataRequest = DescribeInstanceMonitorDataRequest.DescribeInstanceMonitorDataRequest()
        describeInstanceMonitorDataRequest.set_InstanceId(image_id)
        describeInstanceMonitorDataRequest.set_accept_format('json')
        startTime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 300))
        endTime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        describeInstanceMonitorDataRequest.set_StartTime(startTime)
        describeInstanceMonitorDataRequest.set_EndTime(endTime)
        describeInstanceMonitorDataRequest.set_accept_format('json')

        resp = json_decode(client.do_action(describeInstanceMonitorDataRequest))
        result = {}
        result['text'] = 'monitor %s %s from %s to %s' % (region_id, image_id, startTime, endTime)
        result['attachments'] = []

        for i in sorted(resp['MonitorData']['InstanceMonitorData'], key=lambda k: k.get('TimeStamp', 0)):
            iopsread = '-'
            try:
                iopsread   = i['IOPSRead']
                iopswrite  = i['IOPSWrite']
                bpsread    = i['BPSRead']
                bpswrite   = i['BPSWrite']
                internetTX = i['InternetTX']
                internetRX = i['InternetRX']
                intranetTX = i['IntranetTX']
                intranetRX = i['IntranetRX']
            except KeyError:
                pass
            result['attachments'].append({"title": "%s" % i['TimeStamp'], "text":  "IOPSRead: %s\tIOPSWrite: %s\nBPSRead: %s\tBPSWrite: %s\nInternetTX: %s\tInternetRX: %s\nIntranetTX: %s\tIntranetRX: %s\n" % (iopsread, iopswrite, bpsread, bpswrite, internetTX, internetRX, intranetTX, intranetRX)})

        return result
