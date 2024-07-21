from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg
from . import models, forms
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib import messages
from datetime import datetime
from django.conf import settings
from django.urls import reverse_lazy
import stripe
stripe.api_key  = settings.STRIPE_API_KEY

# ===============================================
# index
# ===============================================
class IndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'nagoyameshi/index.html')

index = IndexView.as_view()

# ===============================================
# サブスク : 購入処理のセッションを生成
# ===============================================
class CheckoutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        # セッションを作る
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': settings.STRIPE_PRICE_ID,
                    'quantity': 1,
                },
            ],
            payment_method_types=['card'],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse_lazy("nagoyameshi:success")) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse_lazy("nagoyameshi:index")),
        )

        print(checkout_session['id'])

        return redirect(checkout_session.url)

checkout = CheckoutView.as_view()

# ===============================================
# サブスク : 購入処理の支払い状況を確認
# ===============================================
class SuccessView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        # パラメータにセッションIDがあるかチェック
        if "session_id" not in request.GET:
            print("セッションIDがありません。")
            return redirect("nagoyameshi:index")
        
        # セッションIDが有効であるかチェック
        try:
            checkout_session_id = request.GET['session_id']
            checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)
        except:
            print("このセッションIDは無効です。")
            return redirect("nagoyameshi:index")
        
        print(checkout_session)

        # statusをチェック。未払いであれば拒否する。
        if checkout_session["payment_status"] != "paid":
            print("未払い")
            return redirect("nagoyameshi:index")
        
        print("支払い済み")

        # 有効であれば、セッションIDからカスタマーIDを取得しユーザーモデルに記録する。
        request.user.customer_id = checkout_session["customer"]
        request.user.save()

        print("有料会員登録しました！")
        return redirect("nagoyameshi:premium")

success = SuccessView.as_view()

# ===============================================
# サブスク : ポータルサイトへのリダイレクト
# ===============================================
class PortalView(LoginRequiredMixin, View):
    def get(self, request, *ards, **kwargs):

        if not request.user.customer_id:
            print("有料会員登録されていません")
            return redirect("nagoyameshi:index")
        
        portalSession = stripe.billing_portal.Session.create(
            customer = request.user.customer_id,
            return_url = request.build_absolute_uri(reverse_lazy("nagoyameshi:premium")),
            )

        return redirect(portalSession.url)

portal = PortalView.as_view()

# ===============================================
# サブスク : 有料会員登録ページ/有料会員ページ
# ===============================================
template_inactive = "nagoyameshi/premium_inactive.html"
template_active = "nagoyameshi/premium_active.html"
class PremiumView(View):
    def get(self, request, *args, **kwargs):
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)

        # 有効なら会員のページを表示
        return render(request, template_active)

premium = PremiumView.as_view()

# ===============================================
# top
# ===============================================
class TopView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        # クエリビルダを生成
        query = Q()

        # リクエストから検索条件を取得
        keyword = request.GET.get('keyword')
        selected_category = request.GET.get('category')
        # floor_price = request.GET.get('floor_price')
        # maximum_price = request.GET.get('maximum_price')

        # 検索キーワードがある場合、検索条件を追加
        if keyword:

            words = keyword.replace('　', ' ').split()

            for word in words:
                if word == '':
                    continue
                query &= Q(name__icontains=word)

        # カテゴリが指定されている場合、検索条件に追加
        if selected_category:
            query &= Q(category_id__name__exact=selected_category)
        
        # 下限価格が指定されている場合、検索条件に追加
        form = forms.RestaurantFloorPriceForm(request.GET)
        if form.is_valid():
            cleaned = form.clean()
            query &= Q(floor_price__gte=cleaned['floor_price'])

        # 下限価格が指定されている場合、検索条件に追加
        form = forms.RestaurantMaximumPriceForm(request.GET)
        if form.is_valid():
            cleaned = form.clean()
            query &= Q(maximum_price__lte=cleaned['maximum_price'])
        

        # 条件に合致する店舗を検索
        restaurants = models.Restaurant.objects.filter(query)
        
        context = {'restaurants': restaurants}
        return render(request, 'nagoyameshi/top.html', context)
    
top = TopView.as_view()

# ===============================================
# 店舗詳細
# ===============================================
class RestaurantDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        restaurant = models.Restaurant.objects.get(pk=pk)
        photos = models.RestaurantPhoto.objects.filter(restaurant_id=restaurant)
        favorite = models.Favorite.objects.filter(user_id=request.user, restaurant_id=restaurant).exists()
        context = {'restaurant': restaurant, 'photos':photos, 'favorite':favorite}

        return render(request, 'nagoyameshi/restaurant_detail.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        '''
        お気に入り登録の処理
        '''
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        restaurant = models.Restaurant.objects.get(pk=pk)
        query = Q()
        query &= Q(user_id = request.user)
        query &= Q(restaurant_id = models.Restaurant.objects.get(pk=pk))
        favorite = models.Favorite.objects.filter(query)

        if favorite:
            # 登録されていれば削除し、お気に入り登録を解除
            favorite.delete()
            messages.info(request, 'お気に入り登録を解除しました')
        else:
            # 登録されていなければ、お気に入り登録する
            new_favorite = models.Favorite()
            new_favorite.restaurant_id = models.Restaurant.objects.get(pk=pk)
            new_favorite.user_id = request.user
            new_favorite.save()
            messages.info(request, 'お気に入りに登録しました')

        favorite = models.Favorite.objects.filter(user_id=request.user, restaurant_id=restaurant).exists()
        context = {'restaurant': restaurant, 'favorite':favorite}
        
        return render(request, 'nagoyameshi/restaurant_detail.html', context)

restaurant_detail = RestaurantDetailView.as_view()

# ===============================================
# 店舗ごとのレビュー一覧
# ===============================================
class ReviewListView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        restaurant = models.Restaurant.objects.get(pk=pk)
        review_list = models.Review.objects.filter(restaurant_id=pk)
        context = {'restaurant':restaurant, 'review_list': review_list}
        return render(request, 'nagoyameshi/review_list.html', context)

review_list = ReviewListView.as_view()

# ===============================================
# レビューフォーム
# ===============================================
class ReviewFormView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        form = forms.ReviewForm()
        restaurant = models.Restaurant.objects.get(pk=pk)
        context = {'restaurant':restaurant, 'form': form}
        return render(request, 'nagoyameshi/review_form.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        '''
        レビューの投稿処理
        '''
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        copied = request.POST.copy()
        copied['restaurant_id'] = models.Restaurant.objects.get(pk=pk)
        copied['user_id'] = request.user

        form = forms.ReviewForm(copied)

        print('======form======')
        print(form)

        if form.is_valid():
            # バリデーションOK
            print('投稿完了')
            form.save()
            messages.success(request, 'レビューを投稿しました')
            return redirect('nagoyameshi:review_list', pk=pk)
        
        else:
            # バリデーションNG
            restaurant = models.Restaurant.objects.get(pk=pk)
            context = {'restaurant': restaurant, 'form': form}
 
            # エラーメッセージ
            values = form.errors.get_json_data().values()
            for value in values:
                for v in value:
                    messages.error(request, v["message"])

            return render(request, 'nagoyameshi/review_form.html', context)

review_form = ReviewFormView.as_view()

# ===============================================
# レビュー編集
# ===============================================
class ReviewEditView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            review = models.Review.objects.get(pk=pk,user_id=request.user)
        except:
            return redirect('nagoyameshi:index')
        
        context = {'review':review}
        return render(request, 'nagoyameshi/review_edit.html', context)

    def post(self, request, pk, *args, **kwargs):
        try:
            review = models.Review.objects.get(pk=pk,user_id=request.user)
        except:
            return redirect('nagoyameshi:index')
        
        copied = request.POST.copy()
        copied['user_id'] = review.user_id
        copied['restaurant_id'] = review.restaurant_id

        form = forms.ReviewForm(copied, instance=review)

        if form.is_valid():
            # バリデーションOK
            print('編集完了')
            form.save()
            messages.success(request, 'レビューを編集しました')
            return redirect('nagoyameshi:review_list', pk=review.restaurant_id.pk)
        
        else:
            # バリデーションNG
            review = models.Review.objects.get(pk=pk,user_id=request.user)
            context = {'review':review}
 
            # エラーメッセージ
            values = form.errors.get_json_data().values()
            for value in values:
                for v in value:
                    messages.error(request, v["message"])

            return render(request, 'nagoyameshi/review_edit.html', context)

review_edit = ReviewEditView.as_view()

# ===============================================
# レビュー削除
# ===============================================
class ReviewDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            review = models.Review.objects.get(pk=pk,user_id=request.user)
        except:
            return redirect('nagoyameshi:index')
        
        review.delete()
        return redirect('nagoyameshi:review_list', pk=review.restaurant_id.pk)

review_delete = ReviewDeleteView.as_view()

# ===============================================
# マイページ
# ===============================================
class MypageView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        favorites = models.Favorite.objects.filter(user_id=request.user)
        reservations = models.Reservation.objects.filter(user_id=request.user)
        context = {'favorites': favorites, 'reservations':reservations}
        return render(request, 'nagoyameshi/mypage.html', context)

mypage = MypageView.as_view()

# ===============================================
# 予約フォーム
# ===============================================
class ReservationFormView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        form = forms.ReservationForm()
        restaurant = models.Restaurant.objects.get(pk=pk)
        context = {'restaurant':restaurant, 'form': form}
        return render(request, 'nagoyameshi/reservation_form.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        '''
        予約の申し込み処理
        '''
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        restaurant = models.Restaurant.objects.get(pk=pk)

        copied = request.POST.copy()
        copied['restaurant_id'] = restaurant
        copied['user_id'] = request.user

        form = forms.ReservationForm(copied)

        print('======form======')
        print(type(copied['reservation_datetime']))
        print(copied['reservation_datetime'])

        if form.is_valid():
            # バリデーションOK
            print('予約完了')
            form.save()
            messages.success(request, '予約しました')
            return redirect('nagoyameshi:restaurant_detail', pk=pk)
        
        else:
            # バリデーションNG
            values = form.errors.get_json_data().values()
            for value in values:
                for v in value:
                    messages.error(request, v["message"])

            restaurant = models.Restaurant.objects.get(pk=pk)
            context = {'restaurant': restaurant, 'form': form}

            return render(request, 'nagoyameshi/reservation_form.html', context)

reservation_form = ReservationFormView.as_view()

# ===============================================
# 予約変更
# ===============================================
class ReservationDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        # サブスクが無効なら非会員のページを表示
        if not check_subscription_state(request):
            return render(request, template_inactive)
        
        reservation = models.Reservation.objects.get(pk=pk)
        reservation.delete()
        return redirect('nagoyameshi:mypage')
    
reservation_delete = ReservationDeleteView.as_view()

########

def check_subscription_state(request):
    '''
    サブスクが有効ならTrue、無効ならFalseを返す
    '''
    # カスタマーIDがない場合false
    if not request.user.customer_id:
        print("カスタマーIDがセットされていません")
        return False

    # カスタマーIDをもとにStripeに問い合わせ
    try:
        subscriptions = stripe.Subscription.list(customer=request.user.customer_id)
    except:
        print("このカスタマーIDは無効です。")
        request.user.customer_id = ""
        request.user.save()
        return False
    
    # ステータスがアクティブであるかチェック
    for subscription in subscriptions.auto_paging_iter():
        if subscription.status == "active":
            print("サブスクリプションは有効です。")
            return True
        else:
            print("サブスクリプションが無効です。")

    return False
