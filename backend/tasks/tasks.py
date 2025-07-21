"""
Background task definitions for the e-commerce platform.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Import models
from apps.authentication.models import User
from apps.orders.models import Order
from apps.inventory.models import Inventory, InventoryTransaction
from apps.notifications.models import Notification, NotificationTemplate
from apps.products.models import Product

# Import monitoring utilities
from .monitoring import TaskMonitor, TaskRetryHandler, task_monitor_decorator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def send_email_task(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: Optional[str] = None, template_name: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None):
    """
    Send email asynchronously with retry mechanism and monitoring.
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        html_message: HTML message content
        template_name: Template name for rendering HTML content
        context: Context data for template rendering
    """
    try:
        logger.info(f"Sending email to {recipient_list} with subject: {subject}")
        
        # Render HTML content from template if provided
        if template_name and context:
            html_message = render_to_string(template_name, context)
        
        if html_message:
            # Send HTML email
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            # Send plain text email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False
            )
        
        logger.info(f"Email sent successfully to {recipient_list}")
        return {"status": "success", "recipients": recipient_list}
        
    except Exception as exc:
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def send_sms_task(self, phone_number: str, message: str, template_name: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
    """
    Send SMS notification asynchronously with monitoring.
    
    Args:
        phone_number: Recipient phone number
        message: SMS message content
        template_name: Template name for message rendering
        context: Context data for template rendering
    """
    try:
        logger.info(f"Sending SMS to {phone_number}")
        
        # Render message from template if provided
        if template_name and context:
            message = render_to_string(template_name, context)
        
        # TODO: Integrate with SMS service provider (Twilio, AWS SNS, etc.)
        # For now, we'll log the SMS (replace with actual SMS service integration)
        logger.info(f"SMS Content: {message}")
        
        # Simulate SMS sending
        # In production, replace this with actual SMS service call
        # Example: twilio_client.messages.create(to=phone_number, body=message, from_=settings.TWILIO_PHONE_NUMBER)
        
        logger.info(f"SMS sent successfully to {phone_number}")
        return {"status": "success", "phone_number": phone_number}
        
    except Exception as exc:
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def check_inventory_levels_task(self):
    """
    Check inventory levels and send alerts for low stock items.
    """
    try:
        logger.info("Starting inventory level check")
        
        # Find products with low stock
        low_stock_items = Inventory.objects.filter(
            quantity__lte=models.F('minimum_stock_level')
        ).select_related('product')
        
        if not low_stock_items.exists():
            logger.info("No low stock items found")
            return {"status": "success", "low_stock_count": 0}
        
        # Prepare alert data
        alert_data = []
        for inventory in low_stock_items:
            alert_data.append({
                'product_name': inventory.product.name,
                'product_sku': inventory.product.sku,
                'current_stock': inventory.quantity,
                'minimum_level': inventory.minimum_stock_level,
                'reorder_point': inventory.reorder_point
            })
        
        # Send email alert to administrators
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if admin_emails:
            context = {
                'low_stock_items': alert_data,
                'total_items': len(alert_data),
                'check_time': timezone.now()
            }
            
            send_email_task.delay(
                subject=f"Low Stock Alert - {len(alert_data)} items need attention",
                message=f"There are {len(alert_data)} items with low stock levels.",
                recipient_list=list(admin_emails),
                template_name='emails/inventory_alert.html',
                context=context
            )
            
            # Create in-app notifications for admins
            for admin_id in User.objects.filter(is_staff=True).values_list('id', flat=True):
                Notification.objects.create(
                    user_id=admin_id,
                    title=f"Low Stock Alert - {len(alert_data)} items",
                    message=f"There are {len(alert_data)} items with low stock levels that need attention.",
                    notification_type="INVENTORY_ALERT",
                    reference_id="inventory_alert"
                )
        
        logger.info(f"Inventory check completed. Found {len(alert_data)} low stock items")
        return {"status": "success", "low_stock_count": len(alert_data), "items": alert_data}
        
    except Exception as exc:
        logger.error(f"Inventory check failed: {str(exc)}")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@task_monitor_decorator
def sen
    """
    
    
    Args:
       n for
    """
    try:
        )
        
        
        
        context = {
            'order': order,
            'customer': order.user,
            'order_items': order.items.all(),
         _URL
        }
        
        send_email_task.delay(
            subject=f"Order Confirmation - #{order.order_number}",
            message=f"Your order #{order.order
            recipient_list=[order.user.email],
            template_name='ml',
         
        )
        
        # Create in-app notification
        s.create(
            user=order.user,
            title=f"Order Confirmed - #{order.order",
            message=f"Your order #{order.order_number} has been",
            notification_typN",
            reference_id=str(order.id)
        )
        
        logge")
        return {"status": "success", "order_id": order_id}

:
        logger.error(f"Order {order_id} not found")
        return {"status": "failed", "error": "Order not found"}
    exc
        logger.error(f"Order confirmation email failed: {strc)}")
    
        r


@shared
@task_motor
def send_order_status_update_notification(self, order_id: int, status: str):
    """
    Send order status update notification via email and SMS.
    
    Args:
        order_id: O
        status: New order stus
    """
    try:
        logger.info(f"Sending order status update
        
        =order_id)
        
        # Email notification
        context = {
            'order': order,
            'customer': order.user,
            'new_status': s
         URL
        }
        
        send_email_task.delay(
            subject=f"Order Update - #{order.order_number}",
            message=f"Your order
            recipient_list=[order.user.email],
            template_name='emails/o.html',
            c
        )
        
        # SMS notification if phone number is available
        
            sms_message = f"Yo
            send_sms_task.delay(
                phone_number=order.user.phone,
                message=sms_message
            )
        
        # Create in-app notification
        Notife(
            user=order.user,
}",
,
            notification_type="ORDER_STATUS_UPDATE",
            reference_id=str(order.id)
       )
        
    }")
        rstatus}
        
    exc:
        
        return {"status": "failed", "error": "Order not found"}
    exce
        logger.error(f"Order status update 
        
        return {"st


@shared_t0)
@task_mor
def send_welcome_email(self, u
    """
    Send welcome email to new user.
    
    Args:
        user_id: User ID toil to
    """
    try:
        logger.info(f"Sending welcome email to user {user_id}")
        
        d)
        
        context = {
            'user': user,
            'frontend_url': 
        }
        
        send_email_task.delay(
            s
            message=f"Welcome {user.first_name or user.userm.",


            context=context
        )
        
        # Create welcome notification
       
            user=user,
    ,
         ow!",
            notification_type="WELOME",
            reference_id=str(user.id)
        )
        
        logger.info(f"Welcome e
        return {"status": "success", "user_id": use
       
    excet:
        logger.error(f"User {user_id} not found")
        und"}
    except Exception as exc:
        logger.error(f"Welcome email failed: {str(exc)}")
        , exc)
        return {"status": "failed",r(exc)}


@shared_task(bind=True, max_retries=3, defaultay=60)
@task_monitor_decorator
def process_inventory_transaction(self, invent
                        
                           e):
    """
    Proc.
    
    Args:
        inventory_id: Inventory ID
        transaction_type: Type of transN)
        quantity: Quantity change (positive for OUT)
        reference_number: Reference number forion
        notes: Additional notes
        saction
    """
    try:
        logger.info(f"Processing inventory transaction for inventoory_id}")
        
        inventory = Inventory.objects.select_fo
         None
        
        # Create record
        transaction = InventoryTr
            inventory=inventory,
            transaction_type=transaction_type,
         ty,
        
            notes=notes,
            created_by=user
        )
        
        # Update inventory quantity
        if transaction_type in ['IN', 'RETURN']:
            inventory.quantity += abs(quantity)
        elif T':
            inventory.quantity -= abs(quantity)
:
s
        
        inventory.save()
       
        # Check if stock level is now below minimum and salert
    
         ()
        
       ")
        rn {
            "status": "success", 
        
            "new_quantity": inventory.quantity
        
        
    except Inventory.DoesNotExist:
        logger.error(f"Inventory {inven")
        return {"status"d"}
    except Exception 
        }")
        TaskRetryHandler.retry_task(self, exc)
        return {"status": "failed", "error": str(exc)}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def cleanup_old_notifications(self, days_old: int = 30):
    """
    Clean up old notifications to prevent database bloat.
    
    Args:
        days_old: Number of days old notifications to keep
    """

 days")
        
        cutoff_date = timezone.now() -ys_old)
        
        # Delete old read notifications
       
        te,
            is_read=True
        
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return {"status": "success", "deleted_countcount}
        
    except Excepton as exc:
        logger.error(f"Notification cleanup failed: {str(exc)}")
         exc)
        return {"status": "failed(exc)}


# Import Django models after task definitions to avoid circulimports
from djas


@shared_task(bind=True, max_retries=3, defaul
@task_monitor_decorator
def send_daily_inventory_report(self):
    """
    Send daily inors.
    """
    try:
        logger.info("Generating daily inventory report")
        
        # Get inv
        total_products = Product.objects.fiunt()
        low_str(
            quantity__lte=models.F('minimum_stocel')
        )nt()
        0).count()
        
        # Get top low stock items
        low_stock_items ter(
            quantity__lte=models.Fel')
        ).select_related('product').order_by('quantity')[:10]
        
        # Prepare report data
        report_data = {
            'total_products': totalcts,
            '
        ,
            'low_stock_items': [
                {
        ,
                    'sku': i
                    'current_stock': item.quantity,
                    'minimum_level': item.minimum_sel
                }
             
            ],
date()
   }
        
        # Send report to administrators
       e)
        if admin_emails:
    
         
                message=f"Daily inventory report with {low_stock_count} low stock ims.",
       
        
                context=report_data
         )
            
        admins
            for admin_e):
                Notification.object.create(
                d,
                    title=f"Daily Inventory Report - {timezone.now().date()}",
                    message=f"Daily inventor.",
                    notification_type="I",
                    reference_id="inventory_report"
                )
        
        logger.info("Daily inventory report sent succfully")
        return {"status": "success", "report_data": report_data}
        
    except Exception as exc:
        logger.error(f"Daily inventory repo)
        TaskRetryHandler.retry_task(sc)
        (exc)}


@shared__delay=60)
@task_monitor_decorator
def sync_paymente):
    """
    Sync payment status with payment yments.
    
    Args:
        payment_id: Specific payment ID ments
    """
    try:
        logger.info(f"Syncing payment ''}")
        
        from apps.payyment
        
        if payment_id:
            # Synt
            try:
                payment = Payment.objects.get(id=payment_id, status='')
                payments_to_sync = [payment]
            except Payment.DoesNotExist:
                logger.warning(f"Payment {payment_id} not fou
                retug"}
        else:
            # Get pending payments from last 24 hours
            cutoff_t24)
            payments_to_sync = Payment.objects.filter(
                stat
                created_at__gte=cutoff_time
            ).select_related('order')
        
        synced_count = 0
        failed_cunt = 0
        
        for payment in payments_to_sync:
            try:
        od
                gateway_status = None
                
                if payment.paymen':
                    # Sync with Razorpay
                    gateway_status = syn
         E':
        
                    gateway_
                else:
                    logger.info(f"No sync implement
                    continue
              
                if gateway_status:
onse

                    payment.status = gatews)
       _status
                    
    ED':
         e.now()
                    
        ])
                 
                    logger.info(f"Payment }")
       = 1
        :
                    logger.warning(f"No status upd")
                
            except Exception as e:
        ")
                failed_coun1
        
        logger.info(f"Pay
        return {
            "status": "success", 
        t, 
            "failed_count": failed_count
        }
        
    except Exception as exc:
        logger.error(f"Payment status sync failed: )
        Tc)
        }


def sync_razorpay_p:


    
    Args:
        payment: Payment instance
        
    Retur
        dict: Gateway response wistatus
    """
    try:
        # TODO: Implement actual Razorpay call
       n
        
        
        # Simulate API call
        # In production, this would be:
        y
        # client = razorpayCRET))
        # payment_details = client.paym)
        
        # For now, return a mock response
        return {
        e
            "gateway_payment_id": paymentyment_id,
            "synormat()
        }
        
    except Exception as e:
        l")
        one


def sync_stripe_pay
""
teway.
    
    Args:
       
        
    Returns:
        us
    """
    try:
        # TODO: Implement actual Stripe A call
        
        logger.info(f"Syncing Stripe payment {payment.gateway_payment_id}")
        
        # Simulate API call
        # In production, this would be:
        # import stripe
        # stripe.api_key = settings.STRIPE_SECRET_KEY
        _id)
        
        # For now, return a mock rese
        return {
            "status": "COMPLETED",  # This would come from actuonse
            "gateway_payment_id": payment.gateway_paynt_id,
            "synced_at": timezone.n
        }
        
    except Excep
        logger.error(f"Stripe sync fa
        return None


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@task_monitor_decorator
def send_abandoned_cart_reminders(self):
    """
    Send reminders tts.
    """
    try:
        logger.info("Sending abandoned cart reminders")
        
        from apps.cart.models import Cart
        
        # Find carts tems
        cutoff_time 
        abandoned_carts = Cart.objects.r(
            updated_time,
            items__isnull=False
        ).select_related('user').prefetch_related('items__product').distinct()
        
        reminder_count = 0
        for cart in abandoned_carts:
        :
                # Check if u
                recent_orders = Order.objects.filter(
                    user=cart.user,
                    created_at__gte=cutoff_time
             )
                               if not recent_orders:      )} str(excror":led", "er"faiatus": return {"st       exc)
 sk(self, ry_taeter.rHandlry  TaskRet      )
"r(exc)}std: {ilefaoring nt monitlmerder fulfil(f"Oorerr logger.  :
     on as excpt Excepti    exce
a}
        lert_datrders": aata), "o_dlertlen(a: ed_count"delay", "ccess"suatus": urn {"stret     ")
   rslayed ordeta)} de(alert_dad {leneted. Founring complment monitofulfillfo(f"Order ger.in   log
       
           )
           "ent_delaylmulfilid="order_fence_refer             
       DELAY",FULFILLMENT_pe="ORDER_n_tyotificatio          n          days.",
 max_days} than {or morent fn fulfillmes delayed iorder_data)}  {len(alertThere arege=f"sa       mes            rders",
  ota)}_dalert- {len(aert illment Allf"Order Fue=f    titl        ,
        =admin_id user_id        
           create(bjects.on.oati    Notific       ):
     flat=True'id', ist(_l).valuesf=Trueter(is_staffiler.objects. in Usn_id admifor         dmins
   tions for ap notificareate in-ap        # C  
    
           )      ntext
     context=co            
    ',.htmllment_alertilulfder_fe='emails/ormplate_nam          te
      _emails),ist(admin_list=lent    recipi         ",
    days.ays}than {max_dre  moshipped formed but not een confirhave bhat a)} orders tt_dat{len(alerre  age=f"Thereessa  m           
    delayed",a)} ordersen(alert_dat Alert - {llfillmentder Fuct=f"Or subje            
   task.delay(d_email_         sen       
   }
               
  ays: max_ddays'x_     'ma          e.now(),
 e': timezon'check_tim           
     ta),_daen(alert lrders':l_o  'tota             ta,
 t_da: aleryed_orders'     'dela           = {
 context       
     emails: admin_      ift=True)
  fla'email', list().values_staff=True.filter(is_r.objectsls = Usen_emaimi  ads
      ministrator alert to adilma# Send e       
                })
d
     _delayedays': s_delayeday          'dat,
      ated_order.credate': er_'ord               name}",
 ast_er.user.l} {ord_namefirst.user.': f"{order_namestomer    'cu           der.id,
 or'order_id':                 umber,
r.order_nrde or_number':       'orde      end({
   ert_data.app      al      _at).days
pdated.u- order) ne.now((timezo = delayed     days_       ers:
d_ord delayerder inr o     fo= []
   _data      alertta
   alert da # Prepare             
 : 0}
  ed_count", "delay "success"tatus":return {"s         ")
    found ordersdelayedr.info("No    logge    
     s():orders.existayed_if not del 
               r')
elated('use.select_r       )old_date
 threshat__lt=ted_      updaED',
      ONFIRM='C   status
         filter(.objects.ers = Orderlayed_ord       de
 ongd for too lnot shippeed but been confirmhave orders that  # Find   
            
 days)max_edelta(days=.now() - timmezoneate = tieshold_dhr        te
old dathresh tulate the   # Calc   
     ")
     daysax_days} ing {melays exceed dor fllment fulfier ordtoringoniinfo(f"Mer.    logg
       try:"
   ""status
  onfirmed remain in crder should of days an omber  Maximum nu   max_days:
     
    Args:rame.
    ed timefpecifiwithin the sped not shipmed but been confire ers that havor ord
    Monit
    """: int = 3):ysmax_dalf, ment_task(seill_fulfor_orderitdef mondecorator
ask_monitor_y=300)
@tdelaault_retry_3, defax_retries=d=True, m(binred_task


@shaxc)}or": str(eed", "err "failtus":n {"sta retur       lf, exc)
try_task(ser.reandleyHetr      TaskR)}")
  {str(exc: edk failchecry ventory expi.error(f"In     logger exc:
   xception ast E excep     
   data}
   rt_ms": aleata), "itet_d": len(alerntexpiring_couess", ""succ"status":    return {)
     s"ring item)} expit_data{len(alered. Found heck complety cirntory exp(f"Inver.info   logge      
    )
         
          "ryntory_expinved="i_i  reference              ",
    PIRYINVENTORY_EXon_type="ficati      noti             ",
 old} days.eshays_thr{dn ithis expiring wata)} itemrt_d{len(alehere are e=f"T     messag          ",
     )} items_data- {len(alertpiry Alert Extory nven title=f"I                 min_id,
  er_id=ad         us           create(
bjects.ation.ootific          Nue):
      ', flat=Tres_list('ide).valu_staff=Truter(is.filbjectsin User.oin_id for adm    ns
        mir adfoations notific-app  # Create in             
               )
      context
 ntext=  co            t.html',
  _expiry_alers/inventoryil='emaamemplate_n       te       mails),
  ist(admin_et_list=lecipien         r",
       ys.d} dahreshol{days_tng within s expiri itemert_data)}len(ale {=f"There ar message      ,
         ing soon"tems expirert_data)} in(allert - {leExpiry Aory "Invent  subject=f          lay(
    sk.del_taai_em  send            
          }
          
  dolhresh: days_thold'thres  'days_         w(),
     zone.noimee': ttim 'check_               data),
lert_ms': len(atetal_i   'to            
 a,_dattems': alert_i  'expiring         = {
      context           mails:
 if admin_e        rue)
 flat=Tail','emlues_list(ue).vais_staff=Trer(bjects.filtils = User.oadmin_ema
        ratorsnist admi to email alert     # Send  
      )
          }y
     il_expir days_unt':til_expiry_undays      '
          ry_date,ntory.expi: invexpiry_date'          'e  tity,
    uannventory.qt_stock': i 'curren         ku,
      roduct.sory.pnt': inveduct_skuro       'p  
       name,.product.oryinvente': ct_nam  'produ           
   a.append({_dat     alert       ()).days
dateezone.now().imte - tpiry_danventory.expiry = (iys_until_ex da          s:
 em expiring_itntory in    for invea = []
    at     alert_d data
   e alertpar    # Pre  
    : 0}
      t"ring_counpiex "",uccess: "satus"n {"stretur     ")
       ms foundg iteNo expirininfo("     logger.    ts():
   g_items.exisirinxpf not e    i    
    uct')
    rodrelated('p   ).select_=0
     gtantity__    qu       
 e(),).datmezone.now(__gt=tiry_date     expi       ld_date,
te=threshopiry_date__l ex          filter(
 ory.objects.ems = Inventpiring_it     exture
   del struc actual moed oned basstto be adjud d nee woul thisf not, # I  ld
     ate fie_dan expiryhas ory model mes Invente: This assu# Not      ld
  ho the thresroachings appexpiry dateh ducts wit pro     # Find     
     reshold)
 ays=days_thtimedelta(dte() + ow().datimezone.nte = threshold_dae
        reshold dat thlate thecual
        # C       ")
 aysshold} dn {days_threpiring withi exmsteentory for ihecking inv"Cnfo(fger.i     logy:
      tr """
 warning
   expiry old for s thresh of dayberhold: Numes_thr    daysArgs:
      
    
   alerts. and sendiry dateg exps approachintem inventory forck i  Che"
      ""0):
int = 3_threshold: ysf, daelry_task(sxpientory_echeck_invrator
def monitor_deco)
@task_delay=300ult_retry_s=3, defaietrrue, max_reind=Tsk(bred_ta

@sha(exc)}
error": strled", ": "faistatus"return {"       , exc)
 (selfetry_taskr.rRetryHandle    Task)}")
     {str(excers failed: cart remindnedandoor(f"Abger.err      log exc:
  n asExceptiot excep      
     er_count}
 : remindder_count"", "remin"success": tatus return {"s
       }")ount {reminder_ct:inders sened cart remdoninfo(f"Abanlogger.          
    }")
  r(e)d}: {st.icart {cartminder for to send re(f"Failed ger.errorog      l
           as e:Exception  except                  
          
   _count += 1minder re                       
              )
                    d)
  =str(cart.ience_id   refer           
          ED_CART",DONe="ABANn_typ notificatio                      !",
 ase nowurch poure yomplet cart. Cn your iingititems wa()} .items.countrthave {casage=f"You          mes            ",
   r Carttems in You"I  title=                  .user,
      user=cart                   
   .create(tscation.objecNotifi                
    oncatin-app notifi i# Create                         
                 )
                context
  ntext=co                      tml',
  reminder.hned_cart_bandoils/ae_name='ema     templat                  ,
 mail][cart.user.epient_list= reci                    ",
    cart.ting in yourems waiou have itessage="Y        m         
       ems!", your itet"Don't forg subject=               
        _task.delay(  send_email                
                  }
                      TEND_URL
  ttings.FRONurl': seontend_     'fr                 ount(),
  s.citem: cart.otal_items'      't               ms
   t 5 iters,  # Show fi)[:5].all( cart.itemsms':te 'cart_i                      ,
 cart': cart           '             user,
ser': cart.     'u                 t = {
  ex  cont        
    
 