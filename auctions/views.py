from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User,Category,Listing,Comment, Bid


def index(request):
    allItems = Listing.objects.filter(isActive=True)
    allcategories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "activeItems": allItems,
        "categories":allcategories,
    })
def addcomment(request, id):
    comment = request.POST['newComment']
    currentuser = request.user
    currentListing = Listing.objects.get(pk=id)
    newComment = Comment(author = currentuser, 
                         listing = currentListing, 
                         message = comment )
    newComment.save()
    return HttpResponseRedirect(reverse('listing', args=(id, )))

def watchlist(request):
    currentUser = request.user
    watchlistItems = currentUser.watchlist.all()
    return render(request, "auctions/watchlist.html",{
        'listing':watchlistItems,
    })

    
def displaycategory(request):
    if request.method == "POST":
        categoryFromForm= request.POST['category']
        category = Category.objects.get(categoryName = categoryFromForm)
        allItems = Listing.objects.filter(isActive=True, category = category)
        allcategories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "activeItems": allItems,
            "categories": allcategories,
        })
def closeauction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isInWatchlist = request.user in listingData.watchlist.all()
    allcomments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html",{
        "details":listingData,
        "isListingInWatchlist": isInWatchlist,
        "allComments": allcomments,
        "isOwner": isOwner,
        "update": True,
        "message": "Congratulations! your auction is closed."
    })

    pass
def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    isInWatchlist = request.user in listingData.watchlist.all()
    allcomments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html",{
        "details":listingData,
        "isListingInWatchlist": isInWatchlist,
        "allComments": allcomments,
        "isOwner": isOwner,
    })

def addbid(request, id):
    # Check if 'newbid' is present in the request.POST dictionary
    currentBid = request.POST.get('newbid', None)
    listing = Listing.objects.get(pk=id)
    isInWatchlist = request.user in listing.watchlist.all()
    currentuser = request.user
    allcomments = Comment.objects.filter(listing=listing)
    isOwner = request.user.username == listing.owner.username

    # Check if 'newbid' is None or an empty string
    if currentBid is not None and currentBid != '':
        if float(currentBid) > float(listing.price.bid):
            updateBid = Bid(user=currentuser, bid=currentBid)
            updateBid.save()
            listing.price = updateBid
            listing.save()
            return render(request, "auctions/listing.html", {
                "details": listing,
                "isListingInWatchlist": isInWatchlist,
                "allComments": allcomments,
                "isOwner": isOwner,
                "updated": True,
                "message": "Bid was updated Successfully",
            })
        else:
            return render(request, "auctions/listing.html", {
                "details": listing,
                "isListingInWatchlist": isInWatchlist,
                "allComments": allcomments,
                "isOwner": isOwner,
                "updated": False,
                "message": "Bid updated failed"
            })
    else:
        # Handle the case when 'newbid' is not present or empty
        return render(request, "auctions/listing.html", {
            "details": listing,
            "isListingInWatchlist": isInWatchlist,
            "allComments": allcomments,
            "isOwner": isOwner,
            "updated": False,
            "message": "Bid was not provided in the form submission."
        })

def removeWatchlist(request,id):
    listingdata = Listing.objects.get(pk=id)
    currentUser = request.user
    listingdata.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse('listing', args=(id, )))
    
def addWatchlist(request,id):
    listingdata = Listing.objects.get(pk=id)
    currentUser = request.user
    listingdata.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse('listing', args=(id, )))
def createListing(request):
    if request.method =="GET":
        categoryData = Category.objects.all()
        return render(request, 'auctions/create.html',{
        "categories":categoryData,
    })
    else:
        title = request.POST['title']
        description = request.POST['description']
        imageURL = request.POST['imageURL']
        price = request.POST['price']
        category = request.POST['category']
        currentOwner = request.user
        currentCategory = Category.objects.get(categoryName = category)
        bid = Bid(bid = float(price), user = currentOwner)
        bid.save()
        newListing = Listing(title=title,
                             description=description,
                             imageURL=imageURL,
                             price = bid,
                             owner=currentOwner,
                             category = currentCategory)
        newListing.save()
        return HttpResponseRedirect(reverse(index))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
